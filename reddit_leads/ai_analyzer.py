import os
import json
import time

import anthropic


SYSTEM_PROMPT = """You are a lead qualification specialist for The Admit Co., an MBA and GMAT admissions consulting firm. Analyze Reddit posts, comments, and DMs to identify prospective clients who may benefit from admissions consulting.

Return ONLY a valid JSON array — no markdown, no explanation, just raw JSON."""


SCORING_PROMPT = """Analyze the following {n} Reddit items from MBA/GMAT communities. For each item extract lead intelligence for an admissions consulting firm.

{items_text}

Return a JSON array with exactly {n} objects in the same order as the input. Each object must have these exact keys:

{{
  "item_index": <1-based int>,
  "applicant_stage": <"Exploring" | "GMAT Preparation" | "Retaking GMAT" | "Applying" | "Waitlisted" | "Admitted" | "Not Applicable">,
  "pain_points": <string describing the person's main struggle, or "None identified">,
  "target_schools": <comma-separated school names, or "Not mentioned">,
  "gmat_gre_score": <e.g. "720 GMAT" or "Not mentioned">,
  "urgency_signals": <deadlines or time pressure, or "None">,
  "interest_in_consulting": <"Yes" | "No" | "Implicit">,
  "lead_score": <integer 1-10>,
  "intent_level": <"Low" | "Medium" | "High">,
  "recommended_outreach": <1-2 sentence suggested reply or DM approach, or "Skip" if score < 4>,
  "reasoning": <1 sentence justifying the score>
}}

Scoring guide:
- 9-10: Directly asks for consultant recommendations, expresses frustration with applications, mentions budget for help, tight deadline
- 7-8: Asking about school strategy, profile evaluation, whether to retake GMAT, applying this cycle
- 5-6: Currently prepping GMAT/GRE, researching schools, 1-2 years out
- 3-4: General MBA curiosity, early exploration, "is an MBA worth it" questions
- 1-2: Memes, one-liners, news links, admitted students helping others, bots

intent_level must match lead_score: 7-10 = High, 4-6 = Medium, 1-3 = Low.

Return ONLY the JSON array."""


def _should_skip(item: dict) -> bool:
    content = item.get("content", "").strip()
    username = item.get("username", "")

    if len(content) < 30:
        return True
    if username.lower().endswith("bot") or username == "AutoModerator":
        return True
    # Link-only: content is just a URL
    if content.startswith("http") and " " not in content:
        return True

    return False


def prefilter(items: list[dict]) -> tuple[list[dict], int]:
    kept = [item for item in items if not _should_skip(item)]
    dropped = len(items) - len(kept)
    return kept, dropped


def _build_prompt(items: list[dict]) -> str:
    items_text = ""
    for i, item in enumerate(items, 1):
        items_text += (
            f"\nItem {i}:\n"
            f"- Type: {item['type']}\n"
            f"- Subreddit: r/{item['subreddit']}\n"
            f"- Post Title: {item['post_title']}\n"
            f"- Content: {item['content'][:800]}\n"
            f"- URL: {item['url']}\n"
            f"- Username: u/{item['username']}\n"
        )
    return SCORING_PROMPT.format(n=len(items), items_text=items_text)


def _empty_analysis(index: int) -> dict:
    return {
        "item_index": index,
        "applicant_stage": "Not Applicable",
        "pain_points": "None identified",
        "target_schools": "Not mentioned",
        "gmat_gre_score": "Not mentioned",
        "urgency_signals": "None",
        "interest_in_consulting": "No",
        "lead_score": 0,
        "intent_level": "Low",
        "recommended_outreach": "Skip",
        "reasoning": "Analysis failed — parse error",
    }


def analyze_batch(client: anthropic.Anthropic, items: list[dict], model: str) -> list[dict]:
    prompt = _build_prompt(items)

    for attempt in range(3):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            analyses = json.loads(raw)
            if len(analyses) != len(items):
                raise ValueError(f"Expected {len(items)} results, got {len(analyses)}")
            return analyses

        except anthropic.RateLimitError:
            wait = 60 * (attempt + 1)
            print(f"  [WARN] Rate limit hit, waiting {wait}s...")
            time.sleep(wait)

        except anthropic.APIStatusError as e:
            print(f"  [WARN] API error ({e.status_code}), attempt {attempt + 1}/3")
            time.sleep(10)

        except (json.JSONDecodeError, ValueError) as e:
            print(f"  [WARN] Parse error on attempt {attempt + 1}/3: {e}")
            if attempt == 2:
                return [_empty_analysis(i + 1) for i in range(len(items))]
            time.sleep(2)

    return [_empty_analysis(i + 1) for i in range(len(items))]


def analyze_all_items(
    items: list[dict],
    batch_size: int = 5,
    model: str = "claude-sonnet-4-6",
) -> list[dict]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY must be set in .env")
    client = anthropic.Anthropic(api_key=api_key)

    # Pre-filter cheap noise before hitting the API
    filtered_items, dropped = prefilter(items)
    print(f"  Pre-filter: kept {len(filtered_items)}, dropped {dropped} low-signal items")

    # Batch and analyze
    enriched = []
    batches = [filtered_items[i:i + batch_size] for i in range(0, len(filtered_items), batch_size)]

    for batch_num, batch in enumerate(batches, 1):
        print(f"  Analyzing batch {batch_num}/{len(batches)} ({len(batch)} items)...")
        analyses = analyze_batch(client, batch, model)

        for item, analysis in zip(batch, analyses):
            enriched.append({**item, **analysis})

        if batch_num < len(batches):
            time.sleep(1)

    # Sort by lead_score desc, then timestamp desc
    enriched.sort(key=lambda x: (x.get("lead_score", 0), x.get("timestamp", "")), reverse=True)
    return enriched
