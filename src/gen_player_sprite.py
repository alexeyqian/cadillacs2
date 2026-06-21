"""
Generates src/content/sprites/player.png
192x256 frames, 10 rows of animations.
Run from src/: python gen_player_sprite.py
"""
import pygame
import sys
import math

pygame.init()

FW, FH = 192, 256   # frame size
COLS    = 6          # max frames per row
ROWS    = 10

sheet = pygame.Surface((FW * COLS, FH * ROWS), pygame.SRCALPHA)
sheet.fill((0, 0, 0, 0))

# ── palette ───────────────────────────────────────────────
SKIN   = (220, 180, 140, 255)
HAIR   = ( 40,  30,  20, 255)
SHIRT  = ( 30,  80, 160, 255)
PANTS  = ( 50,  50, 120, 255)
SHOE   = ( 30,  20,  10, 255)
BELT   = (180, 140,  30, 255)
SHADOW = (  0,   0,   0,  80)
WHITE  = (255, 255, 255, 255)

# Body proportions (no padding — 70 wide, 180 tall, centred in 192x256)
CX = FW // 2        # 96  — horizontal centre
FY = FH             # 256 — feet y (bottom of frame)

HEAD_R  = 22
HEAD_CY = FY - 180 + HEAD_R        # top of head at FY-180
NECK_Y  = HEAD_CY + HEAD_R + 2
TORSO_H = 55
TORSO_Y = NECK_Y + 4
HIP_Y   = TORSO_Y + TORSO_H
LEG_H   = 80
KNEE_Y  = HIP_Y + LEG_H // 2
FOOT_Y  = FY - 4

def draw_head(surf, cx, hy, flip=False):
    pygame.draw.circle(surf, SKIN,   (cx, hy), HEAD_R)
    pygame.draw.circle(surf, HAIR,   (cx, hy - HEAD_R // 3), HEAD_R // 2 + 4)

def draw_torso(surf, cx, ty):
    pygame.draw.rect(surf, SHIRT,  (cx - 18, ty, 36, TORSO_H))
    pygame.draw.rect(surf, BELT,   (cx - 18, ty + TORSO_H - 8, 36, 8))

def draw_legs_idle(surf, cx, hy):
    # left leg
    pygame.draw.line(surf, PANTS, (cx - 8, hy), (cx - 10, KNEE_Y), 10)
    pygame.draw.line(surf, PANTS, (cx - 10, KNEE_Y), (cx - 8, FOOT_Y), 9)
    pygame.draw.rect(surf, SHOE,  (cx - 18, FOOT_Y - 8, 18, 8))
    # right leg
    pygame.draw.line(surf, PANTS, (cx + 8, hy), (cx + 10, KNEE_Y), 10)
    pygame.draw.line(surf, PANTS, (cx + 10, KNEE_Y), (cx + 8, FOOT_Y), 9)
    pygame.draw.rect(surf, SHOE,  (cx + 2,  FOOT_Y - 8, 18, 8))

def draw_arms_idle(surf, cx, ty):
    # left arm
    pygame.draw.line(surf, SKIN, (cx - 18, ty + 5), (cx - 24, ty + 30), 7)
    pygame.draw.line(surf, SKIN, (cx - 24, ty + 30), (cx - 22, ty + 52), 6)
    # right arm
    pygame.draw.line(surf, SKIN, (cx + 18, ty + 5), (cx + 24, ty + 30), 7)
    pygame.draw.line(surf, SKIN, (cx + 24, ty + 30), (cx + 22, ty + 52), 6)

def draw_char_idle(surf, cx, bob=0):
    hy = HEAD_CY + bob
    draw_head(surf, cx, hy)
    draw_torso(surf, cx, TORSO_Y + bob)
    draw_legs_idle(surf, cx, HIP_Y + bob)
    draw_arms_idle(surf, cx, TORSO_Y + bob)

# ── Row helpers ───────────────────────────────────────────
def frame_surf(row, col):
    s = pygame.Surface((FW, FH), pygame.SRCALPHA)
    sheet.blit(s, (col * FW, row * FH))
    return sheet, col * FW, row * FH

def get_frame(row, col):
    """Return a subsurface for drawing into."""
    s = pygame.Surface((FW, FH), pygame.SRCALPHA)
    return s, row, col

def blit_frame(s, row, col):
    sheet.blit(s, (col * FW, row * FH))

# ── ROW 0: idle (4 frames, gentle bob) ───────────────────
for i in range(4):
    s = pygame.Surface((FW, FH), pygame.SRCALPHA)
    bob = int(math.sin(i * math.pi / 2) * 3)
    draw_char_idle(s, CX, bob)
    blit_frame(s, 0, i)

# ── ROW 1: walk (4 frames) ────────────────────────────────
def draw_walk_frame(surf, cx, phase):
    angle = phase * math.pi / 2
    bob   = int(math.sin(angle * 2) * 2)
    hy    = HEAD_CY + bob

    # legs alternating
    lleg_swing = int(math.sin(angle) * 22)
    rleg_swing = -lleg_swing

    draw_head(surf, cx, hy)
    draw_torso(surf, cx, TORSO_Y + bob)

    # left leg
    lkx = cx - 8 + lleg_swing // 2
    pygame.draw.line(surf, PANTS, (cx - 8, HIP_Y + bob),   (lkx, KNEE_Y + bob), 10)
    pygame.draw.line(surf, PANTS, (lkx, KNEE_Y + bob), (lkx - lleg_swing // 3, FOOT_Y), 9)
    pygame.draw.rect(surf, SHOE,  (lkx - lleg_swing // 3 - 10, FOOT_Y - 8, 18, 8))
    # right leg
    rkx = cx + 8 + rleg_swing // 2
    pygame.draw.line(surf, PANTS, (cx + 8, HIP_Y + bob),   (rkx, KNEE_Y + bob), 10)
    pygame.draw.line(surf, PANTS, (rkx, KNEE_Y + bob), (rkx - rleg_swing // 3, FOOT_Y), 9)
    pygame.draw.rect(surf, SHOE,  (rkx - rleg_swing // 3 - 2, FOOT_Y - 8, 18, 8))

    # arms counter-swing
    la = int(math.cos(angle) * 20)
    pygame.draw.line(surf, SKIN, (cx - 18, TORSO_Y + 5 + bob), (cx - 24 + la, TORSO_Y + 35 + bob), 7)
    pygame.draw.line(surf, SKIN, (cx + 18, TORSO_Y + 5 + bob), (cx + 24 - la, TORSO_Y + 35 + bob), 7)

for i in range(4):
    s = pygame.Surface((FW, FH), pygame.SRCALPHA)
    draw_walk_frame(s, CX, i)
    blit_frame(s, 1, i)

# ── ROW 2: run (4 frames) ─────────────────────────────────
def draw_run_frame(surf, cx, phase):
    angle = phase * math.pi / 2
    bob   = int(abs(math.sin(angle * 2)) * 5)

    leg_swing = int(math.sin(angle) * 35)
    hy = HEAD_CY - 5 + bob  # leaning forward slightly

    draw_head(surf, cx, hy)
    # torso leaning forward
    tx = cx + 5
    draw_torso(surf, tx, TORSO_Y - 5 + bob)

    # exaggerated legs
    lkx = cx - 6 + leg_swing // 2
    pygame.draw.line(surf, PANTS, (cx - 6, HIP_Y + bob), (lkx, KNEE_Y + bob), 10)
    pygame.draw.line(surf, PANTS, (lkx, KNEE_Y + bob), (lkx + leg_swing // 4, FOOT_Y), 9)
    pygame.draw.rect(surf, SHOE, (lkx + leg_swing // 4 - 10, FOOT_Y - 8, 18, 8))

    rkx = cx + 6 - leg_swing // 2
    pygame.draw.line(surf, PANTS, (cx + 6, HIP_Y + bob), (rkx, KNEE_Y + bob), 10)
    pygame.draw.line(surf, PANTS, (rkx, KNEE_Y + bob), (rkx - leg_swing // 4, FOOT_Y), 9)
    pygame.draw.rect(surf, SHOE, (rkx - leg_swing // 4 - 2, FOOT_Y - 8, 18, 8))

    la = int(math.cos(angle) * 28)
    pygame.draw.line(surf, SKIN, (tx - 18, TORSO_Y - 5 + bob + 5), (tx - 28 + la, TORSO_Y + 30 + bob), 7)
    pygame.draw.line(surf, SKIN, (tx + 18, TORSO_Y - 5 + bob + 5), (tx + 28 - la, TORSO_Y + 30 + bob), 7)

for i in range(4):
    s = pygame.Surface((FW, FH), pygame.SRCALPHA)
    draw_run_frame(s, CX, i)
    blit_frame(s, 2, i)

# ── ROW 3: jump (3 frames: crouch, airborne, land) ────────
def draw_jump_crouch(surf, cx):
    hy = HEAD_CY + 12
    draw_head(surf, cx, hy)
    draw_torso(surf, cx, TORSO_Y + 12)
    # crouched legs
    pygame.draw.line(surf, PANTS, (cx - 10, HIP_Y + 12), (cx - 22, KNEE_Y + 15), 10)
    pygame.draw.line(surf, PANTS, (cx - 22, KNEE_Y + 15), (cx - 12, FOOT_Y), 9)
    pygame.draw.rect(surf, SHOE, (cx - 22, FOOT_Y - 8, 18, 8))
    pygame.draw.line(surf, PANTS, (cx + 10, HIP_Y + 12), (cx + 22, KNEE_Y + 15), 10)
    pygame.draw.line(surf, PANTS, (cx + 22, KNEE_Y + 15), (cx + 12, FOOT_Y), 9)
    pygame.draw.rect(surf, SHOE, (cx + 6, FOOT_Y - 8, 18, 8))
    draw_arms_idle(surf, cx, TORSO_Y + 12)

def draw_jump_air(surf, cx, lift=50):
    hy = HEAD_CY - lift
    draw_head(surf, cx, hy)
    draw_torso(surf, cx, TORSO_Y - lift)
    # tucked legs
    pygame.draw.line(surf, PANTS, (cx - 10, HIP_Y - lift), (cx - 22, HIP_Y - lift + 30), 10)
    pygame.draw.line(surf, PANTS, (cx - 22, HIP_Y - lift + 30), (cx - 14, HIP_Y - lift + 55), 9)
    pygame.draw.rect(surf, SHOE, (cx - 24, HIP_Y - lift + 47, 18, 8))
    pygame.draw.line(surf, PANTS, (cx + 10, HIP_Y - lift), (cx + 22, HIP_Y - lift + 30), 10)
    pygame.draw.line(surf, PANTS, (cx + 22, HIP_Y - lift + 30), (cx + 14, HIP_Y - lift + 55), 9)
    pygame.draw.rect(surf, SHOE, (cx + 8, HIP_Y - lift + 47, 18, 8))
    # arms up
    pygame.draw.line(surf, SKIN, (cx - 18, TORSO_Y - lift + 5), (cx - 28, TORSO_Y - lift - 10), 7)
    pygame.draw.line(surf, SKIN, (cx + 18, TORSO_Y - lift + 5), (cx + 28, TORSO_Y - lift - 10), 7)

for i, draw_fn in enumerate([draw_jump_crouch, lambda s,c: draw_jump_air(s,c,60), lambda s,c: draw_jump_air(s,c,30)]):
    s = pygame.Surface((FW, FH), pygame.SRCALPHA)
    draw_fn(s, CX)
    blit_frame(s, 3, i)

# ── ROW 4: attack_light (4 frames — right jab) ────────────
def draw_light_attack(surf, cx, phase):
    draw_head(surf, cx, HEAD_CY)
    draw_torso(surf, cx, TORSO_Y)
    draw_legs_idle(surf, cx, HIP_Y)
    # left arm back, right arm punch extending
    ext = [0, 30, 55, 30][phase]
    pygame.draw.line(surf, SKIN, (cx - 18, TORSO_Y + 5), (cx - 26, TORSO_Y + 35), 7)
    pygame.draw.line(surf, SKIN, (cx + 18, TORSO_Y + 5), (cx + 24 + ext, TORSO_Y + 20), 7)
    pygame.draw.circle(surf, SKIN, (cx + 24 + ext, TORSO_Y + 20), 8)

for i in range(4):
    s = pygame.Surface((FW, FH), pygame.SRCALPHA)
    draw_light_attack(s, CX, i)
    blit_frame(s, 4, i)

# ── ROW 5: attack_heavy (4 frames — big spin kick) ────────
def draw_heavy_attack(surf, cx, phase):
    bob = [0, -5, -3, 0][phase]
    draw_head(surf, cx, HEAD_CY + bob)
    draw_torso(surf, cx, TORSO_Y + bob)
    # kick leg extends far right
    ext = [0, 30, 60, 20][phase]
    # standing leg
    pygame.draw.line(surf, PANTS, (cx - 8, HIP_Y + bob), (cx - 10, KNEE_Y), 10)
    pygame.draw.line(surf, PANTS, (cx - 10, KNEE_Y), (cx - 8, FOOT_Y), 9)
    pygame.draw.rect(surf, SHOE, (cx - 18, FOOT_Y - 8, 18, 8))
    # kicking leg
    kx = cx + 10 + ext
    ky = HIP_Y + bob - 20
    pygame.draw.line(surf, PANTS, (cx + 8, HIP_Y + bob), (kx, ky), 10)
    pygame.draw.rect(surf, SHOE, (kx, ky - 8, 22, 10))
    # arms
    pygame.draw.line(surf, SKIN, (cx - 18, TORSO_Y + 5 + bob), (cx - 38, TORSO_Y + 20 + bob), 7)
    pygame.draw.line(surf, SKIN, (cx + 18, TORSO_Y + 5 + bob), (cx + 30, TORSO_Y + 25 + bob), 7)

for i in range(4):
    s = pygame.Surface((FW, FH), pygame.SRCALPHA)
    draw_heavy_attack(s, CX, i)
    blit_frame(s, 5, i)

# ── ROW 6: run_attack — horizontal double feet kick ───────
def draw_run_attack(surf, cx, phase):
    # body airborne leaning forward, both feet kick out to the right
    lift  = [5, 20, 25, 10][phase]
    ext   = [5, 30, 50, 20][phase]
    hy    = HEAD_CY - lift
    ty    = TORSO_Y - lift

    draw_head(surf, cx, hy)
    # body tilted
    pygame.draw.polygon(surf, SHIRT, [
        (cx - 20, ty), (cx + 15, ty - 8),
        (cx + 15, ty + TORSO_H - 8), (cx - 20, ty + TORSO_H)
    ])
    pygame.draw.rect(surf, BELT, (cx - 20, ty + TORSO_H - 8, 35, 8))

    # both legs kicking right
    ky = HIP_Y - lift - 10
    pygame.draw.line(surf, PANTS, (cx - 8, HIP_Y - lift), (cx + 10 + ext, ky),     10)
    pygame.draw.rect(surf, SHOE,  (cx + 10 + ext, ky - 8, 22, 10))
    pygame.draw.line(surf, PANTS, (cx - 4, HIP_Y - lift + 15), (cx + 10 + ext, ky + 18), 10)
    pygame.draw.rect(surf, SHOE,  (cx + 10 + ext, ky + 10, 22, 10))

    # arms trailing back
    pygame.draw.line(surf, SKIN, (cx - 18, ty + 5), (cx - 36, ty + 18), 7)
    pygame.draw.line(surf, SKIN, (cx + 10, ty + 5), (cx + 8,  ty + 22), 7)

for i in range(4):
    s = pygame.Surface((FW, FH), pygame.SRCALPHA)
    draw_run_attack(s, CX, i)
    blit_frame(s, 6, i)

# ── ROW 7: jump_attack — kick downward from peak ──────────
def draw_jump_attack(surf, cx, phase):
    # body at jump peak, right leg kicks downward
    lift   = [55, 60, 45, 20][phase]
    kd_ext = [0,  30, 60, 40][phase]   # downward extension of kick

    hy = HEAD_CY - lift
    ty = TORSO_Y - lift

    draw_head(surf, cx, hy)
    draw_torso(surf, cx, ty)

    hip_y = HIP_Y - lift

    # standing leg tucked
    pygame.draw.line(surf, PANTS, (cx - 8, hip_y), (cx - 20, hip_y + 25), 10)
    pygame.draw.rect(surf, SHOE,  (cx - 28, hip_y + 20, 18, 8))

    # kicking leg plunging down-right
    kfx = cx + 20
    kfy = hip_y + 20 + kd_ext
    pygame.draw.line(surf, PANTS, (cx + 8, hip_y), (kfx, kfy), 10)
    pygame.draw.rect(surf, SHOE,  (kfx - 4, kfy, 22, 10))

    # arms spread for balance
    pygame.draw.line(surf, SKIN, (cx - 18, ty + 5), (cx - 36, ty + 15), 7)
    pygame.draw.line(surf, SKIN, (cx + 18, ty + 5), (cx + 36, ty + 15), 7)

for i in range(4):
    s = pygame.Surface((FW, FH), pygame.SRCALPHA)
    draw_jump_attack(s, CX, i)
    blit_frame(s, 7, i)

# ── ROW 8: hurt (3 frames) ────────────────────────────────
def draw_hurt(surf, cx, phase):
    stagger = [-8, 8, -4][phase]
    draw_head(surf, cx + stagger, HEAD_CY + 5)
    draw_torso(surf, cx + stagger // 2, TORSO_Y + 5)
    draw_legs_idle(surf, cx + stagger // 2, HIP_Y + 5)
    # arms flung back
    pygame.draw.line(surf, SKIN, (cx - 16 + stagger, TORSO_Y + 8), (cx - 36 + stagger, TORSO_Y + 20), 7)
    pygame.draw.line(surf, SKIN, (cx + 16 + stagger, TORSO_Y + 8), (cx + 36 + stagger, TORSO_Y + 20), 7)

for i in range(3):
    s = pygame.Surface((FW, FH), pygame.SRCALPHA)
    draw_hurt(s, CX, i)
    blit_frame(s, 8, i)

# ── ROW 9: die (4 frames) ─────────────────────────────────
def draw_die(surf, cx, phase):
    drop = [0, 20, 45, 70][phase]
    tilt  = [0, 15, 35, 0][phase]  # tilt head

    if phase < 3:
        hy = HEAD_CY + drop
        draw_head(surf, cx - tilt // 2, hy)
        draw_torso(surf, cx, TORSO_Y + drop)
        draw_legs_idle(surf, cx, HIP_Y + drop)
        # arms drooping
        pygame.draw.line(surf, SKIN, (cx - 18, TORSO_Y + drop + 5), (cx - 30, TORSO_Y + drop + 40), 7)
        pygame.draw.line(surf, SKIN, (cx + 18, TORSO_Y + drop + 5), (cx + 30, TORSO_Y + drop + 40), 7)
    else:
        # lying on ground — draw horizontal
        gy = FOOT_Y - 18
        pygame.draw.ellipse(surf, PANTS, (cx - 40, gy - 10, 80, 20))
        pygame.draw.circle(surf, SKIN, (cx + 40, gy - 5), HEAD_R - 4)
        pygame.draw.ellipse(surf, SHIRT, (cx - 35, gy - 8, 75, 16))

for i in range(4):
    s = pygame.Surface((FW, FH), pygame.SRCALPHA)
    draw_die(s, CX, i)
    blit_frame(s, 9, i)

# ── Save ──────────────────────────────────────────────────
out = "content/sprites/player.png"
pygame.image.save(sheet, out)
print(f"Saved {FW*COLS}x{FH*ROWS} sprite sheet → {out}")
pygame.quit()
