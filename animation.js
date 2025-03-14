const canvas = document.getElementById('bouncingBall');
const ctx = canvas.getContext('2d');

// Set canvas size
canvas.width = 800;
canvas.height = 600;

// Ball properties
const ball = {
    x: canvas.width / 2,
    y: canvas.height / 2,
    radius: 25,
    dx: 5,
    dy: 0,
    gravity: 0.5,
    friction: 0.99,
    bounce: 0.8,
    rotation: 0,
    rotationSpeed: 0
};

// Ground properties
const ground = {
    y: canvas.height - 100,
    height: 100
};

// Park elements
const trees = [
    { x: 100, y: ground.y - 150, size: 80 },
    { x: 300, y: ground.y - 180, size: 100 },
    { x: 500, y: ground.y - 160, size: 90 },
    { x: 700, y: ground.y - 140, size: 70 }
];

const clouds = [
    { x: 50, y: 100, size: 60, speed: 0.5 },
    { x: 200, y: 80, size: 80, speed: 0.3 },
    { x: 400, y: 120, size: 70, speed: 0.4 },
    { x: 600, y: 90, size: 65, speed: 0.6 }
];

// Draw functions
function drawBall() {
    ctx.save();
    ctx.translate(ball.x, ball.y);
    ctx.rotate(ball.rotation);

    // Draw ball shadow
    ctx.beginPath();
    ctx.arc(0, ground.y - ball.y + 5, ball.radius * 0.8, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
    ctx.fill();
    ctx.closePath();

    // Draw ball body
    ctx.beginPath();
    ctx.arc(0, 0, ball.radius, 0, Math.PI * 2);
    const gradient = ctx.createRadialGradient(-5, -5, 0, 0, 0, ball.radius);
    gradient.addColorStop(0, '#ffffff');
    gradient.addColorStop(0.5, '#4CAF50');
    gradient.addColorStop(1, '#2E7D32');
    ctx.fillStyle = gradient;
    ctx.fill();
    ctx.closePath();

    // Draw ball pattern
    ctx.beginPath();
    ctx.arc(0, 0, ball.radius * 0.8, 0, Math.PI * 2);
    ctx.strokeStyle = '#1B5E20';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.closePath();

    ctx.restore();
}

function drawTree(x, y, size) {
    // Draw trunk
    ctx.fillStyle = '#5D4037';
    ctx.fillRect(x - 10, y - size/2, 20, size/2);

    // Draw leaves
    ctx.beginPath();
    ctx.arc(x, y - size/2, size/2, 0, Math.PI * 2);
    ctx.fillStyle = '#2E7D32';
    ctx.fill();
    ctx.closePath();
}

function drawCloud(x, y, size) {
    ctx.beginPath();
    ctx.arc(x, y, size/2, 0, Math.PI * 2);
    ctx.arc(x + size/2, y, size/3, 0, Math.PI * 2);
    ctx.arc(x - size/2, y, size/3, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.fill();
    ctx.closePath();
}

function drawGround() {
    // Draw grass
    ctx.fillStyle = '#81C784';
    ctx.fillRect(0, ground.y, canvas.width, ground.height);

    // Draw grass details
    for(let i = 0; i < 100; i++) {
        const x = Math.random() * canvas.width;
        const y = ground.y + Math.random() * ground.height;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + Math.random() * 10 - 5, y - Math.random() * 5);
        ctx.strokeStyle = '#2E7D32';
        ctx.lineWidth = 1;
        ctx.stroke();
    }
}

// Animation loop
function animate() {
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw sky
    const skyGradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    skyGradient.addColorStop(0, '#87CEEB');
    skyGradient.addColorStop(1, '#E0F7FA');
    ctx.fillStyle = skyGradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw clouds
    clouds.forEach(cloud => {
        cloud.x += cloud.speed;
        if(cloud.x > canvas.width + 100) cloud.x = -100;
        drawCloud(cloud.x, cloud.y, cloud.size);
    });

    // Draw trees
    trees.forEach(tree => drawTree(tree.x, tree.y, tree.size));

    // Draw ground
    drawGround();

    // Update ball position and rotation
    ball.dy += ball.gravity;
    ball.dx *= ball.friction;
    ball.dy *= ball.friction;
    ball.rotation += ball.rotationSpeed;

    ball.x += ball.dx;
    ball.y += ball.dy;

    // Ball collision with walls
    if (ball.x + ball.radius > canvas.width) {
        ball.x = canvas.width - ball.radius;
        ball.dx *= -ball.bounce;
        ball.rotationSpeed = -ball.dx * 0.1;
    }
    if (ball.x - ball.radius < 0) {
        ball.x = ball.radius;
        ball.dx *= -ball.bounce;
        ball.rotationSpeed = -ball.dx * 0.1;
    }

    // Ball collision with ground
    if (ball.y + ball.radius > ground.y) {
        ball.y = ground.y - ball.radius;
        ball.dy *= -ball.bounce;
        ball.dx *= 0.99;
        ball.rotationSpeed = ball.dx * 0.1;
    }

    // Draw ball
    drawBall();

    // Continue animation
    requestAnimationFrame(animate);
}

// Start animation
animate();

// Add mouse interaction
canvas.addEventListener('click', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    // Calculate direction and speed
    const angle = Math.atan2(mouseY - ball.y, mouseX - ball.x);
    const speed = 15;
    
    ball.dx = Math.cos(angle) * speed;
    ball.dy = Math.sin(angle) * speed;
    ball.rotationSpeed = ball.dx * 0.1;
}); 