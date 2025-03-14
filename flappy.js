// Get the canvas element from HTML
const canvas = document.getElementById('gameCanvas');
// Get the 2D rendering context for the canvas
const ctx = canvas.getContext('2d');
// Get DOM elements for score and game over display
const scoreElement = document.getElementById('score');
const gameOverElement = document.getElementById('gameOver');
const finalScoreElement = document.getElementById('finalScore');

// Set the canvas dimensions
canvas.width = 400;  // Width of the game area
canvas.height = 600; // Height of the game area

// Define game constants that control the physics and gameplay
const GRAVITY = 0.25;        // Reduced gravity for slower falling
const FLAP_SPEED = -5;       // Gentler flap for more control
const PIPE_SPEED = 1.0;      // Slower pipe movement
const PIPE_SPACING = 250;    // Much wider gap between pipes
const PIPE_WIDTH = 50;       // Slightly thinner pipes
const BIRD_SIZE = 25;        // Slightly smaller bird for easier navigation

// Game state variables
let gameStarted = false;     // Whether the game has started
let gameOver = false;        // Whether the game has ended
let score = 0;              // Current score
let highScore = 0;          // Best score achieved

// Create the bird object with its properties and methods
const bird = {
    x: canvas.width / 4,     // Bird's horizontal position
    y: canvas.height / 2,    // Bird's vertical position
    velocity: 0,            // Bird's current vertical speed
    rotation: 0,            // Bird's current rotation angle

    // Method to draw the bird on the canvas
    draw() {
        // Save the current canvas state
        ctx.save();
        // Move the drawing context to the bird's position
        ctx.translate(this.x, this.y);
        // Rotate the drawing context by the bird's rotation
        ctx.rotate(this.rotation);

        // Draw the bird's body (yellow circle)
        ctx.beginPath();
        ctx.arc(0, 0, BIRD_SIZE/2, 0, Math.PI * 2);
        ctx.fillStyle = '#FFD700';  // Gold color
        ctx.fill();
        ctx.closePath();

        // Draw the bird's eye (black circle)
        ctx.beginPath();
        ctx.arc(5, -5, 5, 0, Math.PI * 2);
        ctx.fillStyle = 'black';
        ctx.fill();
        ctx.closePath();

        // Draw the bird's beak (orange triangle)
        ctx.beginPath();
        ctx.moveTo(10, 0);
        ctx.lineTo(20, 0);
        ctx.lineTo(15, 5);
        ctx.closePath();
        ctx.fillStyle = '#FFA500';  // Orange color
        ctx.fill();
        ctx.closePath();

        // Draw the velocity indicator (red line)
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(0, this.velocity * 2);
        ctx.strokeStyle = 'rgba(255, 0, 0, 0.5)';  // Semi-transparent red
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.closePath();

        // Restore the canvas state
        ctx.restore();
    },

    // Method to make the bird flap
    flap() {
        this.velocity = FLAP_SPEED;  // Set upward velocity
        this.rotation = -0.5;        // Tilt bird upward
    },

    // Method to update bird's position and physics
    update() {
        this.velocity += GRAVITY;    // Apply gravity
        this.y += this.velocity;     // Update position
        // Update rotation based on velocity (limit rotation angle)
        this.rotation = Math.min(Math.PI/2, Math.max(-Math.PI/2, this.velocity * 0.1));

        // Check if bird hits the ground
        if (this.y + BIRD_SIZE/2 > canvas.height) {
            gameOver = true;  // End game if bird hits ground
        }
    }
};

// Array to store all pipes in the game
let pipes = [];

// Function to create a new pipe
function createPipe() {
    // Calculate random position for the gap between pipes
    // Make the gap position more predictable by limiting the range
    const gapY = Math.random() * (canvas.height - PIPE_SPACING - 200) + 100;
    // Add new pipe to the pipes array
    pipes.push({
        x: canvas.width,     // Start pipe at right edge of canvas
        gapY: gapY,         // Position of the gap
        passed: false,      // Whether bird has passed this pipe

        // Method to draw the pipe
        draw() {
            // Draw dashed guide lines
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.moveTo(this.x, 0);
            ctx.lineTo(this.x, this.gapY);
            ctx.moveTo(this.x, this.gapY + PIPE_SPACING);
            ctx.lineTo(this.x, canvas.height);
            ctx.stroke();
            ctx.setLineDash([]);

            // Draw the top pipe (green rectangle)
            ctx.fillStyle = '#2E7D32';
            ctx.fillRect(this.x, 0, PIPE_WIDTH, this.gapY);
            
            // Draw the bottom pipe (green rectangle)
            ctx.fillRect(this.x, this.gapY + PIPE_SPACING, PIPE_WIDTH, canvas.height);
            
            // Draw pipe edges (darker green)
            ctx.fillStyle = '#1B5E20';
            ctx.fillRect(this.x - 5, 0, 5, this.gapY);
            ctx.fillRect(this.x - 5, this.gapY + PIPE_SPACING, 5, canvas.height);

            // Draw safe zone indicator (semi-transparent green)
            ctx.fillStyle = 'rgba(0, 255, 0, 0.1)';
            ctx.fillRect(this.x, this.gapY, PIPE_WIDTH, PIPE_SPACING);
        },

        // Method to update pipe position and check collisions
        update() {
            this.x -= PIPE_SPEED;    // Move pipe left
            
            // Add more forgiving collision detection
            if (bird.x + BIRD_SIZE/2 > this.x && 
                bird.x - BIRD_SIZE/2 < this.x + PIPE_WIDTH) {
                // Add a small buffer zone for collisions
                const buffer = 5;
                if (bird.y - BIRD_SIZE/2 + buffer < this.gapY || 
                    bird.y + BIRD_SIZE/2 - buffer > this.gapY + PIPE_SPACING) {
                    gameOver = true;  // End game if bird hits pipe
                }
            }
            
            // Update score when passing pipe
            if (!this.passed && this.x + PIPE_WIDTH < bird.x) {
                score++;
                this.passed = true;
                scoreElement.textContent = `Score: ${score}`;
            }
        }
    });
}

// Main game loop function
function gameLoop() {
    // Handle game over state
    if (gameOver) {
        if (score > highScore) {
            highScore = score;
        }
        finalScoreElement.textContent = score;
        gameOverElement.style.display = 'block';
        return;
    }

    // Clear the canvas for new frame
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw sky background
    ctx.fillStyle = '#87CEEB';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw ground
    ctx.fillStyle = '#8B4513';
    ctx.fillRect(0, canvas.height - 50, canvas.width, 50);

    // Update and draw pipes
    pipes = pipes.filter(pipe => pipe.x > -PIPE_WIDTH);  // Remove off-screen pipes
    pipes.forEach(pipe => {
        pipe.update();
        pipe.draw();
    });

    // Create new pipes when needed
    if (pipes.length === 0 || pipes[pipes.length - 1].x < canvas.width - 200) {
        createPipe();
    }

    // Update and draw bird
    bird.update();
    bird.draw();

    // Draw start screen instructions
    if (!gameStarted) {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = 'white';
        ctx.font = '24px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Click or Press Space to Start', canvas.width/2, canvas.height/2);
        ctx.font = '16px Arial';
        ctx.fillText('Guide the bird through the green zones', canvas.width/2, canvas.height/2 + 40);
    }

    // Request next frame
    requestAnimationFrame(gameLoop);
}

// Add keyboard event listener for space key
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space') {
        if (!gameStarted) {
            gameStarted = true;
            gameLoop();
        }
        if (!gameOver) {
            bird.flap();
            // Add double flap option for extra boost
            setTimeout(() => {
                if (!gameOver) {
                    bird.flap();
                }
            }, 50);
        }
    }
});

// Add click event listener for mouse/touch input
canvas.addEventListener('click', () => {
    if (!gameStarted) {
        gameStarted = true;
        gameLoop();
    }
    if (!gameOver) {
        bird.flap();
        // Add double flap option for extra boost
        setTimeout(() => {
            if (!gameOver) {
                bird.flap();
            }
        }, 50);
    }
});

// Function to restart the game
function restartGame() {
    gameStarted = false;
    gameOver = false;
    score = 0;
    scoreElement.textContent = 'Score: 0';
    gameOverElement.style.display = 'none';
    pipes = [];
    bird.y = canvas.height / 2;
    bird.velocity = 0;
    bird.rotation = 0;
    gameLoop();
}

// Start the game loop
gameLoop(); 