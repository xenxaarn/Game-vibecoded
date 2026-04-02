import pygame
import random
import math
import sys
import json
import os

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1000, 700
FPS = 60
BASE_SHIP_SPEED = 8
BULLET_SPEED = 12
ENEMY_BULLET_SPEED = 5
BOSS_BULLET_SPEED = 7

# Colors
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 120, 0)
WHITE = (255, 255, 255)
BG_CORE = (2, 2, 10) # Darker space
GOLD = (255, 215, 0)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
DARK_RED = (80, 0, 0)

# Setup Screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NOVA STRIKER - Deep Space Edition")
clock = pygame.time.Clock()

LEADERBOARD_FILE = "leaderboard.json"
SETTINGS_FILE = "settings.json"

# Fonts
try:
    font_main = pygame.font.SysFont("Orbitron", 80, bold=True)
    font_hud = pygame.font.SysFont("Rajdhani", 30, bold=True)
    font_mono = pygame.font.SysFont("Courier New", 18, bold=True)
    font_credits = pygame.font.SysFont("Rajdhani", 24, bold=True)
except:
    font_main = pygame.font.Font(None, 80)
    font_hud = pygame.font.Font(None, 30)
    font_mono = pygame.font.Font(None, 18)
    font_credits = pygame.font.Font(None, 24)

class Bullet:
    def __init__(self, x, y, angle=0, size=5, color=CYAN, is_enemy=False, damage=1, speed_mult=1):
        self.x = x
        self.y = y
        self.speed = (ENEMY_BULLET_SPEED if is_enemy else BULLET_SPEED) * speed_mult
        if is_enemy and damage > 5: self.speed = BOSS_BULLET_SPEED
        
        self.vx = math.sin(math.radians(angle)) * self.speed
        self.vy = math.cos(math.radians(angle)) * self.speed if is_enemy else -math.cos(math.radians(angle)) * self.speed
        self.size = size
        self.color = color
        self.is_enemy = is_enemy
        self.damage = damage

    def update(self):
        self.x += self.vx
        self.y += self.vy
        return -50 <= self.x <= WIDTH + 50 and -50 <= self.y <= HEIGHT + 50

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.size // 2)

class Enemy:
    def __init__(self, level):
        self.x = random.randint(100, WIDTH - 100)
        self.y = -100
        self.speed = random.uniform(2, 4) + (level * 0.05) # Slower speed scaling
        self.health = 1 + (level // 10)
        self.max_health = self.health
        self.is_boss = False
        self.shoot_timer = random.randint(30, 200)

    def update(self, bullets):
        self.y += self.speed
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            bullets.append(Bullet(self.x, self.y + 20, 0, size=6, color=ORANGE, is_enemy=True))
            self.shoot_timer = random.randint(150, 400)
        return self.y < HEIGHT + 100

    def draw(self, surface):
        pts = [(self.x, self.y + 40), (self.x - 15, self.y), (self.x + 15, self.y)]
        pygame.draw.polygon(surface, RED, pts)
        pygame.draw.rect(surface, WHITE, (self.x - 10, self.y - 10, 20, 30), border_radius=3)
        if self.max_health > 1:
            pygame.draw.rect(surface, (50, 0, 0), (self.x - 15, self.y - 15, 30, 4))
            pygame.draw.rect(surface, RED, (self.x - 15, self.y - 15, 30 * (self.health/self.max_health), 4))

class Boss:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = -300
        self.target_y = 150
        self.health = 1000
        self.max_health = 1000
        self.is_boss = True
        self.dir = 1
        self.speed = 5
        self.shoot_timer = 0
        self.anger = 0
        self.eye_pulse = 0

    def update(self, bullets):
        self.eye_pulse = (self.eye_pulse + 0.1) % (math.pi * 2)
        if self.y < self.target_y:
            self.y += 2
        else:
            self.anger = 1.0 - (self.health / self.max_health)
            self.x += (self.speed + (self.anger * 4)) * self.dir
            if self.x > WIDTH - 200 or self.x < 200:
                self.dir *= -1
            
            self.shoot_timer += 1
            rate = 40 if self.anger < 0.5 else 25
            if self.shoot_timer % rate == 0:
                angles = [-30, -15, 0, 15, 30] if self.anger < 0.7 else [-45, -30, -15, 0, 15, 30, 45]
                for a in angles:
                    bullets.append(Bullet(self.x + a, self.y + 100, a, size=15, color=RED, is_enemy=True, damage=25))
        return True

    def draw(self, surface):
        shake_x = random.randint(-int(self.anger*8), int(self.anger*8))
        shake_y = random.randint(-int(self.anger*8), int(self.anger*8))
        bx, by = self.x + shake_x, self.y + shake_y
        # Main Body
        pygame.draw.polygon(surface, RED, [(bx, by + 160), (bx - 140, by - 40), (bx + 140, by - 40)])
        pygame.draw.rect(surface, WHITE, (bx - 70, by - 120, 140, 160), border_radius=15)
        
        # Health Bar Background (with Border)
        pygame.draw.rect(surface, WHITE, (WIDTH//2 - 402, HEIGHT - 42, 804, 24), 2)
        pygame.draw.rect(surface, (50, 0, 0), (WIDTH//2 - 400, HEIGHT - 40, 800, 20))
        # Fill
        fill_w = max(0, int(800 * (max(0, self.health)/self.max_health)))
        pygame.draw.rect(surface, RED, (WIDTH//2 - 400, HEIGHT - 40, fill_w, 20))
        
        # Angry Spikes
        for sx in [-80, -40, 40, 80]:
            pygame.draw.polygon(surface, RED, [(bx + sx, by - 120), (bx + sx - 15, by - 180), (bx + sx + 15, by - 180)])
        eye_glow = int(150 + math.sin(self.eye_pulse) * 105)
        eye_color = (eye_glow, 0, 0)
        pygame.draw.circle(surface, eye_color, (int(bx - 35), int(by - 60)), 15)
        pygame.draw.circle(surface, eye_color, (int(bx + 35), int(by - 60)), 15)
        pygame.draw.circle(surface, WHITE, (int(bx - 35), int(by - 60)), 5)
        pygame.draw.circle(surface, WHITE, (int(bx + 35), int(by - 60)), 5)
        
        txt = font_hud.render("DEATH-SKULL ANNIHILATOR", True, RED)
        surface.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT - 75))

class Pickup:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 3

    def update(self):
        self.y += self.speed
        return self.y < HEIGHT

    def draw(self, surface):
        pygame.draw.circle(surface, GOLD, (int(self.x), int(self.y)), 12)
        txt = font_mono.render("AMMO", True, BG_CORE)
        surface.blit(txt, (self.x - 24, self.y - 8))

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-10, 10)
        self.vy = random.uniform(-10, 10)
        self.life = 60
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        return self.life > 0

    def draw(self, surface):
        alpha = int((self.life / 60) * 255)
        s = pygame.Surface((6, 6), pygame.SRCALPHA)
        pygame.draw.rect(s, (*self.color, alpha), (0, 0, 6, 6))
        surface.blit(s, (self.x, self.y))

class BGRock:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(-HEIGHT, HEIGHT)
        self.size = random.uniform(20, 60)
        self.speed = random.uniform(1, 3)
        self.rot = random.uniform(0, 360)
        self.rot_speed = random.uniform(-2, 2)
        # Random jagged shape
        self.points = []
        num_pts = 8
        for i in range(num_pts):
            angle = (i / num_pts) * 360
            dist = self.size * random.uniform(0.7, 1.3)
            self.points.append((math.sin(math.radians(angle)) * dist, math.cos(math.radians(angle)) * dist))

    def update(self):
        self.y += self.speed
        self.rot += self.rot_speed
        if self.y > HEIGHT + 100:
            self.y = -100
            self.x = random.randint(0, WIDTH)
        return True

    def draw(self, surface):
        # Apply rotation to points
        draw_pts = []
        for p in self.points:
            rx = p[0] * math.cos(math.radians(self.rot)) - p[1] * math.sin(math.radians(self.rot))
            ry = p[0] * math.sin(math.radians(self.rot)) + p[1] * math.cos(math.radians(self.rot))
            draw_pts.append((rx + self.x, ry + self.y))
        pygame.draw.polygon(surface, (40, 40, 50), draw_pts)
        pygame.draw.polygon(surface, (60, 60, 75), draw_pts, 2)

class Game:
    def __init__(self):
        self.state = 'LOGIN'
        self.player_name = ""
        self.px = WIDTH // 2
        self.py = HEIGHT - 100
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.pickups = []
        self.particles = []
        
        self.health = 100
        self.ammo = 100
        self.level = 1
        self.score = 0
        self.kills = 0
        self.invincible = 0
        
        # Cheats & Power-ups
        self.unlimited_ammo = False
        self.god_mode = False
        self.is_cloaked = False
        self.ship_speed_mult = 1.0
        self.turbo_mode = False
        self.nonstop_mode = False
        self.weapon_mode = 0 # 0:Normal, 1:Heavy, 2:Rapid, 3:Spread
        self.cheat_input = ""
        self.last_cheat_result = ""
        self.cheat_feedback_timer = 0
        self.unlock_msg = ""
        self.unlock_timer = 0
        
        self.controls = self.load_settings()
        self.remapping = None 
        
        self.leaderboard = self.load_leaderboard()
        
        # Realistic Background Elements
        self.stars_far = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(0.5, 1)] for _ in range(100)]
        self.stars_mid = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(1.2, 2)] for _ in range(60)]
        self.stars_near = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(3, 5)] for _ in range(30)]
        self.bg_rocks = [BGRock() for _ in range(10)]
        
        # Nebula Clusters
        self.nebulas = []
        for _ in range(5):
            surf = pygame.Surface((400, 400), pygame.SRCALPHA)
            color = random.choice([(40, 0, 60, 20), (0, 30, 60, 20), (40, 20, 0, 20)])
            for i in range(15):
                r = random.randint(100, 200)
                cx, cy = random.randint(100, 300), random.randint(100, 300)
                pygame.draw.circle(surf, color, (cx, cy), r)
            self.nebulas.append({"surf": surf, "x": random.randint(-150, WIDTH), "y": random.randint(-150, HEIGHT), "speed": random.uniform(0.2, 0.4)})
        
        self.victory_timer = 0

    def load_leaderboard(self):
        if os.path.exists(LEADERBOARD_FILE):
            try:
                with open(LEADERBOARD_FILE, 'r') as f: return json.load(f)
            except: return {}
        return {}

    def save_leaderboard(self):
        with open(LEADERBOARD_FILE, 'w') as f: json.dump(self.leaderboard, f)

    def load_settings(self):
        defaults = {"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "shoot": pygame.K_SPACE}
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f: return json.load(f)
            except: return defaults
        return defaults

    def save_settings(self):
        with open(SETTINGS_FILE, 'w') as f: json.dump(self.controls, f)

    def reset(self, full=True):
        self.score = 0
        self.kills = 0
        self.level = 1
        self.health = 100
        self.ammo = 100
        self.enemies = []
        self.bullets = []
        self.enemy_bullets = []
        self.pickups = []
        self.particles = []
        self.px = WIDTH // 2
        self.invincible = 90
        self.ship_speed_mult = 1.0
        self.victory_timer = 0

    def update(self):
        # Background Movement (Parallax)
        for n in self.nebulas:
            n["y"] += n["speed"]
            if n["y"] > HEIGHT: n["y"] = -400
        for s in self.stars_far:
            s[1] += s[2]
            if s[1] > HEIGHT: s[1] = 0
        for s in self.stars_mid:
            s[1] += s[2]
            if s[1] > HEIGHT: s[1] = 0
        for s in self.stars_near:
            s[1] += s[2]
            if s[1] > HEIGHT: s[1] = 0
        for r in self.bg_rocks:
            r.update()

        if self.state in ['SETTINGS', 'CHEAT_CONSOLE', 'PAUSED']: return
        self.particles = [p for p in self.particles if p.update()]

        if self.state == 'VICTORY':
            self.victory_timer += 1
            if self.victory_timer % 5 == 0:
                self.particles.append(Particle(random.randint(0, WIDTH), random.randint(0, HEIGHT), random.choice([GOLD, CYAN, MAGENTA, WHITE, GREEN])))
            return

        if self.state != 'PLAYING': return

        if self.invincible > 0: self.invincible -= 1
        if self.cheat_feedback_timer > 0: self.cheat_feedback_timer -= 1
        if self.unlock_timer > 0: self.unlock_timer -= 1

        keys = pygame.key.get_pressed()
        speed = BASE_SHIP_SPEED * self.ship_speed_mult
        if keys[self.controls["left"]] and self.px > 40: self.px -= speed
        if keys[self.controls["right"]] and self.px < WIDTH - 40: self.px += speed

        # Auto-fire for Rapid mode or Turbo cheat
        if self.weapon_mode == 2 and keys[self.controls["shoot"]]:
            if random.random() < 0.2: self.shoot()
        
        # Turbo Cheat: Hold Ctrl to blast everything
        if self.turbo_mode and (pygame.key.get_mods() & pygame.KMOD_CTRL):
            if random.random() < 0.3: self.shoot() 
        
        # Nonstop Cheat: Automatic 24/7 weapons fire
        if self.nonstop_mode:
            if random.random() < 0.2: self.shoot()

        self.bullets = [b for b in self.bullets if b.update()]
        self.enemy_bullets = [b for b in self.enemy_bullets if b.update()]

        if self.invincible <= 0 and not self.is_cloaked:
            for b in self.enemy_bullets[:]:
                if math.sqrt((b.x - self.px)**2 + (b.y - self.py)**2) < 30:
                    self.take_damage(b.damage)
                    if b in self.enemy_bullets: self.enemy_bullets.remove(b)

            for e in self.enemies[:]:
                if math.sqrt((e.x - self.px)**2 + (e.y - self.py)**2) < 50:
                    self.take_damage(34 if not e.is_boss else 100)
                    if not e.is_boss and e in self.enemies: self.enemies.remove(e)

        for e in self.enemies[:]:
            if not e.update(self.enemy_bullets): self.enemies.remove(e); continue
            for b in self.bullets[:]:
                dist = math.sqrt((e.x - b.x)**2 + (e.y - b.y)**2)
                if dist < (100 if e.is_boss else 40):
                    e.health -= b.damage
                    if b in self.bullets: self.bullets.remove(b)
                    if e.health <= 0:
                        for _ in range(20 if not e.is_boss else 100):
                            self.particles.append(Particle(e.x, e.y, RED if e.is_boss else ORANGE))
                        
                        if e in self.enemies: self.enemies.remove(e)
                        self.score += 50000 if e.is_boss else 150
                        self.kills += 1
                        
                        
                        if e.is_boss: 
                            self.state = 'VICTORY'
                            self.save_player_score()
                        
                        if random.random() > 0.4: self.pickups.append(Pickup(e.x, e.y))
                        
                        old_lvl = self.level
                        self.level = min(50, (self.kills // 50) + 1)
                        
                        # Weapon Unlocks
                        if old_lvl < 10 <= self.level:
                            self.weapon_mode = 2 # RAPID
                            self.unlock_msg = "RAPID LASER SYSTEM UNLOCKED"
                            self.unlock_timer = 180
                        elif old_lvl < 30 <= self.level:
                            self.weapon_mode = 3 # SPREAD
                            self.unlock_msg = "SPREAD FIRE ARRAY UNLOCKED"
                            self.unlock_timer = 180
                        elif old_lvl < 49 <= self.level:
                            self.weapon_mode = 1 # HEAVY
                            self.unlock_msg = "HEAVY CANNON ARCHITECTURE UNLOCKED"
                            self.unlock_timer = 180
                            
                        if self.level == 50 and not any(en.is_boss for en in self.enemies):
                            self.enemies.append(Boss())
                        break

        for p in self.pickups[:]:
            if not p.update(): self.pickups.remove(p); continue
            if math.sqrt((p.x - self.px)**2 + (p.y - self.py)**2) < 35:
                self.ammo += 50; self.pickups.remove(p)

        if not any(en.is_boss for en in self.enemies) and self.level < 50:
            if random.random() < 0.02 + (self.level * 0.006): self.enemies.append(Enemy(self.level))

    def take_damage(self, amt):
        if self.god_mode: return
        self.health -= amt; self.invincible = 45 
        if self.health <= 0: self.state = 'GAME_OVER'; self.save_player_score()

    def save_player_score(self):
        if self.player_name not in self.leaderboard:
            self.leaderboard[self.player_name] = {"high_score": 0, "history": [], "games_played": 0}
        profile = self.leaderboard[self.player_name]
        profile["games_played"] += 1; profile["history"].append(int(self.score))
        if self.score > profile["high_score"]: profile["high_score"] = int(self.score)
        profile["history"] = sorted(profile["history"], reverse=True)[:5]; self.save_leaderboard()

    def shoot(self):
        if self.ammo > 0 or self.unlimited_ammo:
            if self.weapon_mode == 1: # HEAVY
                self.bullets.append(Bullet(self.px, self.py - 20, 0, size=20, color=ORANGE, damage=10, speed_mult=0.6))
                if not self.unlimited_ammo: self.ammo -= 3
            elif self.weapon_mode == 2: # RAPID
                self.bullets.append(Bullet(self.px, self.py, 0, size=4, color=CYAN, speed_mult=1.5))
                if not self.unlimited_ammo: self.ammo -= 0.5
            elif self.weapon_mode == 3: # SPREAD
                self.bullets.append(Bullet(self.px - 25, self.py, -10, color=MAGENTA))
                self.bullets.append(Bullet(self.px, self.py, 0, size=8, color=CYAN))
                self.bullets.append(Bullet(self.px + 25, self.py, 10, color=MAGENTA))
                if not self.unlimited_ammo: self.ammo -= 2
            else: # NORMAL
                self.bullets.append(Bullet(self.px, self.py, 0))
                if not self.unlimited_ammo: self.ammo -= 1

    def draw(self):
        screen.fill(BG_CORE)
        
        # Parallax Background Layers
        for n in self.nebulas: screen.blit(n["surf"], (n["x"], n["y"]))
        for s in self.stars_far: pygame.draw.circle(screen, (80, 80, 100), (int(s[0]), int(s[1])), 1)
        for s in self.stars_mid: pygame.draw.circle(screen, (130, 130, 160), (int(s[0]), int(s[1])), 2)
        for r in self.bg_rocks: r.draw(screen)
        for s in self.stars_near: pygame.draw.circle(screen, (200, 200, 255), (int(s[0]), int(s[1])), 3)
        
        for p in self.particles: p.draw(screen)

        if self.state in ['PLAYING', 'PAUSED']:
            for p in self.pickups: p.draw(screen)
            for b in self.bullets: b.draw(screen)
            for b in self.enemy_bullets: b.draw(screen)
            for e in self.enemies: e.draw(screen)
            ship_color = (100, 100, 255, 120) if self.is_cloaked else CYAN
            if self.invincible % 10 < 5:
                pygame.draw.polygon(screen, ship_color, [(self.px, self.py - 35), (self.px - 30, self.py + 15), (self.px + 30, self.py + 15)])
                pygame.draw.rect(screen, WHITE, (self.px - 10, self.py, 20, 15))
                if random.random() > 0.3: pygame.draw.circle(screen, MAGENTA, (self.px, self.py + 30), random.randint(8, 18))
            self.draw_ui()
            if self.cheat_feedback_timer > 0:
                msg = font_hud.render(self.last_cheat_result, True, GOLD)
                screen.blit(msg, (WIDTH//2 - msg.get_width()//2, 100))
            if self.unlock_timer > 0:
                msg = font_hud.render(self.unlock_msg, True, CYAN)
                screen.blit(msg, (WIDTH//2 - msg.get_width()//2, 140))
        
        if self.state == 'VICTORY':
            self.draw_overlay("THE GALAXY IS SAVED", "DEATH-SKULL HAS BEEN PURGED", "")
            v_msg = font_main.render("MISSION COMPLETE", True, GOLD)
            screen.blit(v_msg, (WIDTH//2 - v_msg.get_width()//2, 100))
            al = font_main.render("DESIGNED BY ALYAAN", True, CYAN)
            screen.blit(al, (WIDTH//2 - al.get_width()//2, HEIGHT - 200))
        elif self.state == 'LOGIN':
            self.draw_overlay("NOVA STRIKER", "IDENTIFY PILOT", self.player_name, "[TAB] SETTINGS  |  [CTRL+TAB] CHEATS")
        elif self.state == 'START':
            self.draw_overlay("SYSTEMS ARMED", "[SPACE] TO INITIATE", "REACH LEVEL 50 TO FACE THE SKULL")
        elif self.state == 'GAME_OVER':
            self.draw_overlay("PILOT ELIMINATED", f"FINAL SCORE: {self.score}", "[R] TO REBOOT")
        elif self.state == 'SETTINGS': self.draw_settings()
        elif self.state == 'CHEAT_CONSOLE': self.draw_cheat_console()
        elif self.state == 'PAUSED': self.draw_overlay("SYSTEMS PAUSED", "MISSION ON HOLD", "[ESC] TO RESUME")

    def draw_ui(self):
        hud = pygame.Surface((WIDTH, 80), pygame.SRCALPHA)
        pygame.draw.rect(hud, (255, 255, 255, 40), (0, 0, WIDTH, 80)); screen.blit(hud, (0, 0))
        pygame.draw.rect(screen, (50, 0, 0), (20, 15, 250, 20), border_radius=5)
        h_color = GREEN if self.health > 50 else (ORANGE if self.health > 25 else RED)
        pygame.draw.rect(screen, h_color, (20, 15, 2.5 * max(0, self.health), 20), border_radius=5)
        screen.blit(font_mono.render(f"HULL INTEGRITY: {int(max(0, self.health))}%", True, WHITE), (20, 40))
        ammo_txt = "UNLIMITED" if self.unlimited_ammo else str(int(self.ammo))
        screen.blit(font_hud.render(f"AMMO: {ammo_txt}", True, GOLD), (WIDTH - 240, 15))
        screen.blit(font_hud.render(f"LVL {self.level}", True, MAGENTA), (WIDTH - 240, 45))
        screen.blit(font_hud.render(f"SCORE: {self.score}", True, WHITE), (WIDTH//2 - 60, 10))
        creds = font_credits.render("CREATED BY ALYAAN", True, GOLD)
        screen.blit(creds, (WIDTH//2 - creds.get_width()//2, 45))

    def draw_overlay(self, t1, t2, t3, t4=""):
        s = pygame.Surface((WIDTH, HEIGHT)); s.set_alpha(180); s.fill((0, 0, 0)); screen.blit(s, (0, 0))
        m1 = font_main.render(t1, True, CYAN)
        m2 = font_hud.render(t2, True, WHITE)
        m3 = font_hud.render(t3, True, MAGENTA)
        screen.blit(m1, (WIDTH//2 - m1.get_width()//2, 250))
        p = int(200 + 55 * math.sin(pygame.time.get_ticks() * 0.005))
        creds = font_credits.render("DESIGNED & DEVELOPED BY ALYAAN", True, (p, p//2, 0))
        screen.blit(creds, (WIDTH//2 - creds.get_width()//2, HEIGHT - 80))
        screen.blit(m2, (WIDTH//2 - m2.get_width()//2, 380))
        screen.blit(m3, (WIDTH//2 - m3.get_width()//2, 450))
        if t4:
            m4 = font_mono.render(t4, True, GOLD); screen.blit(m4, (WIDTH//2 - m4.get_width()//2, 580))

    def draw_settings(self):
        s = pygame.Surface((WIDTH, HEIGHT)); s.set_alpha(235); s.fill((0, 5, 15)); screen.blit(s, (0, 0))
        t = font_main.render("CONTROL DECK", True, CYAN); screen.blit(t, (WIDTH//2 - t.get_width()//2, 80))
        for i, action in enumerate(["left", "right", "shoot"]):
            color = GOLD if self.remapping == action else WHITE; y = 250 + i * 80
            pygame.draw.rect(screen, (255,255,255,20), (WIDTH//2 - 300, y - 10, 600, 60), border_radius=5)
            key_name = pygame.key.name(self.controls[action]).upper()
            if self.remapping == action: key_name = "> PRESS ANY KEY <"
            screen.blit(font_hud.render(f"{action.upper()}:", True, CYAN), (WIDTH//2 - 250, y))
            screen.blit(font_hud.render(key_name, True, color), (WIDTH//2 + 50, y))
        h = font_mono.render("CLICK TO REMAP | [TAB] TO SAVE & EXIT", True, MAGENTA)
        screen.blit(h, (WIDTH//2 - h.get_width()//2, HEIGHT - 100))

    def draw_cheat_console(self):
        s = pygame.Surface((WIDTH, HEIGHT)); s.set_alpha(250); s.fill((0, 10, 5)); screen.blit(s, (0, 0))
        pygame.draw.rect(screen, (0, 255, 0), (WIDTH//2 - 350, HEIGHT//2 - 50, 700, 100), 1)
        t = font_hud.render("PILOT COMMAND OVERRIDE", True, (0, 255, 0)); screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 90))
        txt = font_main.render(self.cheat_input + "_", True, (0, 255, 0)); screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 30))
        h = font_mono.render("ENTER CODE OR [CTRL+TAB] TO ABORT", True, WHITE); screen.blit(h, (WIDTH//2 - h.get_width()//2, HEIGHT//2 + 120))
        al = font_credits.render("SYS-ADMIN: ALYAAN", True, GOLD); screen.blit(al, (WIDTH - 180, HEIGHT - 40))

    def process_cheat(self):
        code = self.cheat_input.upper(); self.cheat_feedback_timer = 120
        if code == "WARP50": 
            self.kills = 2450 # Matches 50 kills per level scaling
            self.level = 50
            self.weapon_mode = 1 
            self.enemies = [Boss()]
            self.last_cheat_result = "OVERRIDE: BOSS CONTACT | HEAVY ARMED"
        elif code == "AMMOBOX": self.unlimited_ammo = not self.unlimited_ammo; self.last_cheat_result = f"AMMO LINK: {self.unlimited_ammo}"
        elif code == "GODMODE": self.god_mode = not self.god_mode; self.last_cheat_result = f"GOD MODE: {self.god_mode}"
        elif code == "VANISH": self.is_cloaked = not self.is_cloaked; self.last_cheat_result = f"CLOAK: {self.is_cloaked}"
        elif code == "SPEEDUP": self.ship_speed_mult = 2.0 if self.ship_speed_mult == 1.0 else 1.0; self.last_cheat_result = f"BOOST: {self.ship_speed_mult > 1}"
        elif code == "TURBO":
            self.turbo_mode = not self.turbo_mode
            self.last_cheat_result = f"TURBO FIRE: {'ACTIVE' if self.turbo_mode else 'OFF'}"
        elif code == "NONSTOP":
            self.nonstop_mode = not self.nonstop_mode
            self.last_cheat_result = f"NONSTOP FIRE: {'ACTIVE' if self.nonstop_mode else 'OFF'}"
        elif code in ["HEAVY", "RAPID", "SPREAD"]:
            self.weapon_mode = {"HEAVY": 1, "RAPID": 2, "SPREAD": 3}[code]
            self.last_cheat_result = f"WEAPON: {code} CONFIGURED"
        elif code == "NORMAL":
            self.unlimited_ammo = False
            self.god_mode = False
            self.is_cloaked = False
            self.ship_speed_mult = 1.0
            self.turbo_mode = False
            self.nonstop_mode = False
            self.weapon_mode = 0
            self.last_cheat_result = "FACTORY SPECS: ALL CHEATS DISABLED"
        else: self.last_cheat_result = "ERROR: INVALID COMMAND"
        self.cheat_input = ""

def main():
    game = Game()
    while True:
        mx, my = pygame.mouse.get_pos(); mods = pygame.key.get_mods()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and game.state == 'SETTINGS':
                for i, action in enumerate(["left", "right", "shoot"]):
                    y = 250 + i * 80
                    if WIDTH//2 - 300 < mx < WIDTH//2 + 300 and y - 10 < my < y + 60: game.remapping = action
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game.state == 'PLAYING': game.state = 'PAUSED'
                    elif game.state == 'PAUSED': game.state = 'PLAYING'
                if (mods & pygame.KMOD_CTRL) and event.key == pygame.K_TAB:
                    game.state = 'CHEAT_CONSOLE' if game.state != 'CHEAT_CONSOLE' else 'PLAYING'; game.cheat_input = ""; continue
                if game.state == 'CHEAT_CONSOLE':
                    if event.key == pygame.K_RETURN: game.process_cheat(); game.state = 'PLAYING'
                    elif event.key == pygame.K_BACKSPACE: game.cheat_input = game.cheat_input[:-1]
                    elif event.key not in [pygame.K_TAB, pygame.K_LCTRL, pygame.K_RCTRL]:
                        if len(game.cheat_input) < 15: game.cheat_input += event.unicode.upper()
                elif game.state == 'SETTINGS':
                    if game.remapping: game.controls[game.remapping] = event.key; game.remapping = None; game.save_settings()
                    elif event.key == pygame.K_TAB: game.state = 'LOGIN'
                elif game.state == 'LOGIN':
                    if event.key == pygame.K_TAB: game.state = 'SETTINGS'
                    elif event.key == pygame.K_RETURN and game.player_name: game.state = 'START'
                    elif event.key == pygame.K_BACKSPACE: game.player_name = game.player_name[:-1]
                    else:
                        if len(game.player_name) < 12 and event.unicode.isalnum(): game.player_name += event.unicode.upper()
                elif game.state == 'START':
                    if event.key == pygame.K_SPACE: game.state = 'PLAYING'
                elif game.state == 'PLAYING':
                    if event.key == game.controls["shoot"] and game.weapon_mode != 2: game.shoot()
                elif game.state in ['GAME_OVER', 'VICTORY']:
                    if event.key == pygame.K_r: game.reset(full=True); game.state = 'PLAYING'
        game.update(); game.draw(); pygame.display.flip(); clock.tick(FPS)

if __name__ == "__main__": main()
