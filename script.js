const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const scoreElement = document.getElementById('score');
const multiplierElement = document.getElementById('multiplier');
const startScreen = document.getElementById('start-screen');
const gameOverScreen = document.getElementById('game-over-screen');
const finalScoreElement = document.getElementById('final-score');
const finalMultiplierElement = document.getElementById('final-multiplier');
const startButton = document.getElementById('start-button');
const restartButton = document.getElementById('restart-button');

// Game constants
const LANES = 3;
const LANE_WIDTH = 200;
const GAME_SPEED_START = 5;
const SPEED_INCREMENT = 0.0005;

// Game state
let gameState = 'START'; // START, PLAYING, GAME_OVER
let score = 0;
let multiplier = 1;
let speed = GAME_SPEED_START;
let distance = 0;
let gridOffset = 0;
let screenShake = 0;

// Particle system
let particles = [];
function createParticle(x, y, color, size = 5) {
    return {
        x, y,
        vx: (Math.random() - 0.5) * 10,
        vy: (Math.random() - 0.5) * 10,
        life: 1.0,
        decay: 0.02 + Math.random() * 0.03,
        color,
        size
    };
}

// Player object
const player = {
    lane: 1, // 0, 1, 2
    targetLane: 1,
    x: 0,
    y: 0,
    width: 60,
    height: 40,
    color: '#00ffff',
    glowColor: 'rgba(0, 255, 255, 0.5)',
    laneTransitionSpeed: 0.15
};

// Obstacle pool
let obstacles = [];

// Handle sizing
function resize() {
    const container = canvas.parentElement;
    canvas.width = container.clientWidth * window.devicePixelRatio;
    canvas.height = container.clientHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
}

window.addEventListener('resize', resize);
resize();

// Input handling
window.addEventListener('keydown', (e) => {
    if (gameState !== 'PLAYING') return;

    if (e.key === 'ArrowLeft' && player.targetLane > 0) {
        player.targetLane--;
    } else if (e.key === 'ArrowRight' && player.targetLane < LANES - 1) {
        player.targetLane++;
    }
});

// Game logic
function initGame() {
    score = 0;
    multiplier = 1;
    speed = GAME_SPEED_START;
    distance = 0;
    obstacles = [];
    player.lane = 1;
    player.targetLane = 1;
    updateUI();
}

function updateUI() {
    scoreElement.textContent = Math.floor(score).toLocaleString('en-US', { minimumIntegerDigits: 6 });
    multiplierElement.textContent = `x${multiplier}`;
}

function createObstacle() {
    const lane = Math.floor(Math.random() * LANES);
    const types = ['CUBE', 'PYRAMID'];
    const type = types[Math.floor(Math.random() * types.length)];

    obstacles.push({
        lane: lane,
        z: 2000, // Distance from camera
        type: type,
        size: 50,
        color: Math.random() > 0.5 ? '#ff00ff' : '#ffff00'
    });
}

function update() {
    if (gameState !== 'PLAYING') return;

    // Update speed and distance
    speed += SPEED_INCREMENT;
    distance += speed;
    gridOffset = (gridOffset + speed) % 100;

    // Update score
    score += (speed / 10) * multiplier;
    updateUI();

    // Smooth lane transition
    player.lane += (player.targetLane - player.lane) * player.laneTransitionSpeed;

    // Afterburner particles
    const playerX = canvas.width / (2 * window.devicePixelRatio) + ((player.lane - 1) * LANE_WIDTH * 2);
    const playerY = canvas.height / window.devicePixelRatio * 0.85;
    if (Math.random() > 0.5) {
        particles.push(createParticle(playerX - 15, playerY + 20, '#00ffff', 3));
        particles.push(createParticle(playerX + 15, playerY + 20, '#00ffff', 3));
    }

    // Update particles
    for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.life -= p.decay;
        if (p.life <= 0) particles.splice(i, 1);
    }

    // Screen shake decay
    if (screenShake > 0) screenShake *= 0.9;

    // Update obstacles
    for (let i = obstacles.length - 1; i >= 0; i--) {
        const obs = obstacles[i];
        obs.z -= speed * 10;

        // Collision detection (approximate 3D to 2D)
        if (obs.z < 100 && obs.z > 0) {
            if (Math.abs(obs.lane - player.lane) < 0.3) {
                screenShake = 20;
                // Explosion particles
                for (let k = 0; k < 20; k++) particles.push(createParticle(playerX, playerY, '#ff00ff', 10));
                gameOver();
            }
        }

        if (obs.z < -100) {
            obstacles.splice(i, 1);
            multiplier = Math.min(10, multiplier + 0.1);
        }
    }

    // Spawn obstacles
    if (Math.random() < 0.02 + (speed * 0.001)) {
        createObstacle();
    }
}

function draw() {
    const w = canvas.width / window.devicePixelRatio;
    const h = canvas.height / window.devicePixelRatio;

    ctx.save();
    if (screenShake > 1) {
        ctx.translate((Math.random() - 0.5) * screenShake, (Math.random() - 0.5) * screenShake);
    }

    ctx.clearRect(0, 0, w, h);

    // Draw Background Gradient
    const gradient = ctx.createRadialGradient(w / 2, h / 3, 0, w / 2, h / 3, h);
    gradient.addColorStop(0, '#1a0a2e');
    gradient.addColorStop(1, '#050510');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, w, h);

    // Draw Retro Sun
    drawSun(w, h);

    // Draw Grid (Perspective)
    drawGrid(w, h);

    // Draw Obstacles
    drawObstacles(w, h);

    // Draw Player
    drawPlayer(w, h);

    // Draw Particles
    drawParticles();

    ctx.restore();
}

function drawParticles() {
    particles.forEach(p => {
        ctx.globalAlpha = p.life;
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2);
        ctx.fill();
    });
    ctx.globalAlpha = 1;
}

function drawSun(w, h) {
    const sunX = w / 2;
    const sunY = h * 0.35;
    const sunRadius = 120;

    ctx.save();
    const sunGlow = ctx.createRadialGradient(sunX, sunY, sunRadius * 0.8, sunX, sunY, sunRadius * 1.5);
    sunGlow.addColorStop(0, '#ff8c00');
    sunGlow.addColorStop(1, 'transparent');
    ctx.fillStyle = sunGlow;
    ctx.beginPath();
    ctx.arc(sunX, sunY, sunRadius * 1.5, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#ff8c00';
    ctx.beginPath();
    ctx.arc(sunX, sunY, sunRadius, 0, Math.PI, true);
    ctx.lineTo(sunX - sunRadius, sunY);
    ctx.fill();

    // Horizon lines in sun
    ctx.strokeStyle = '#050510';
    ctx.lineWidth = 4;
    for (let i = 0; i < 8; i++) {
        const y = sunY - (i * 15);
        if (y > sunY - sunRadius) {
            ctx.beginPath();
            ctx.moveTo(sunX - sunRadius, y);
            ctx.lineTo(sunX + sunRadius, y);
            ctx.stroke();
        }
    }
    ctx.restore();
}

function drawGrid(w, h) {
    const horizonY = h * 0.5;
    const gridW = w * 2;
    ctx.strokeStyle = '#ff00ff';
    ctx.lineWidth = 1;
    ctx.globalAlpha = 0.5;

    // Horizontal lines
    for (let i = 0; i < 20; i++) {
        const z = (i * 50 - gridOffset) % 1000;
        if (z < 0) continue;
        const y = horizonY + (h - horizonY) * (100 / (z / 5 + 100));
        ctx.beginPath();
        ctx.moveTo(w / 2 - gridW, y);
        ctx.lineTo(w / 2 + gridW, y);
        ctx.stroke();
    }

    // Vertical lines (Perspective)
    const numLines = 20;
    for (let i = -numLines; i <= numLines; i++) {
        const xOffset = i * 100;
        ctx.beginPath();
        ctx.moveTo(w / 2 + xOffset / 10, horizonY);
        ctx.lineTo(w / 2 + xOffset * 5, h);
        ctx.stroke();
    }
    ctx.globalAlpha = 1;
}

function drawPlayer(w, h) {
    const horizonY = h * 0.5;
    const playerZ = 100;
    const laneX = (player.lane - 1) * LANE_WIDTH;

    // Project 3D to 2D
    const screenX = w / 2 + (laneX * 2);
    const screenY = h * 0.85;

    ctx.save();
    ctx.shadowBlur = 20;
    ctx.shadowColor = player.color;
    ctx.fillStyle = player.color;

    // Draw sci-fi ship shape
    ctx.beginPath();
    ctx.moveTo(screenX, screenY - 20);
    ctx.lineTo(screenX - 30, screenY + 20);
    ctx.lineTo(screenX + 30, screenY + 20);
    ctx.closePath();
    ctx.fill();

    // Afterburners
    ctx.fillStyle = '#ffffff';
    ctx.shadowColor = '#ffffff';
    ctx.beginPath();
    ctx.arc(screenX - 15, screenY + 22, 5, 0, Math.PI * 2);
    ctx.arc(screenX + 15, screenY + 22, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
}

function drawObstacles(w, h) {
    const horizonY = h * 0.5;

    obstacles.forEach(obs => {
        const laneX = (obs.lane - 1) * LANE_WIDTH;
        const scale = 200 / (obs.z + 200);
        const screenX = w / 2 + (laneX * scale * 10);
        const screenY = horizonY + (h - horizonY) * (scale);
        const size = obs.size * scale;

        ctx.save();
        ctx.shadowBlur = 15;
        ctx.shadowColor = obs.color;
        ctx.fillStyle = obs.color;

        if (obs.type === 'CUBE') {
            ctx.fillRect(screenX - size / 2, screenY - size, size, size);
        } else {
            ctx.beginPath();
            ctx.moveTo(screenX, screenY - size);
            ctx.lineTo(screenX - size / 2, screenY);
            ctx.lineTo(screenX + size / 2, screenY);
            ctx.closePath();
            ctx.fill();
        }
        ctx.restore();
    });
}

function gameOver() {
    gameState = 'GAME_OVER';
    gameOverScreen.classList.remove('hidden');
    finalScoreElement.textContent = Math.floor(score).toLocaleString();
    finalMultiplierElement.textContent = `x${multiplier.toFixed(1)}`;
}

function gameLoop() {
    update();
    draw();
    requestAnimationFrame(gameLoop);
}

startButton.addEventListener('click', () => {
    startScreen.classList.add('hidden');
    gameState = 'PLAYING';
    initGame();
});

restartButton.addEventListener('click', () => {
    gameOverScreen.classList.add('hidden');
    gameState = 'PLAYING';
    initGame();
});

// Start loop
gameLoop();
