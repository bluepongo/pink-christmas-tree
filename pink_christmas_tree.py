# -*- coding: utf-8 -*-
"""
淡粉色粒子螺旋圣诞树（参考抖音风格：纯黑星空 + 粉色螺旋粒子圣诞树 + 树顶爱心）
依赖: pip install pygame
操作:
  - 鼠标拖动: 手动旋转/俯仰
  - 空格: 暂停/继续自动旋转
  - ESC 或关闭窗口: 退出
圣诞元素: 螺旋彩带、树顶爱心、圣诞球挂饰、礼物盒、飘雪、星空闪烁、Merry Christmas 文字
"""

import math
import random
import sys

import pygame

# ---------------- 基础配置 ----------------
WIDTH, HEIGHT = 1080, 720
FPS = 60
BG_COLOR = (4, 4, 8)                     # 近纯黑背景

AUTO_ROTATE_SPEED = 0.45

# 树几何（局部坐标: y 向上，原点在树底中心）
TREE_HEIGHT = 5.2
TREE_BASE_RADIUS = 2.2
GROUND_RADIUS = 3.1

# 粒子数量
N_CLOUD = 4200        # 树体雾状粒子云
N_HELIX = 1400        # 螺旋彩带
N_GROUND = 1800       # 底部裙摆
N_BAUBLE = 46         # 圣诞球挂饰
N_STARS = 150         # 背景星空
N_SNOW = 110          # 飘雪
N_GIFT_EDGE = 14      # 每条礼物盒棱的采样数

# 配色
PINK_CLOUD = [(255, 175, 205), (255, 160, 195), (255, 190, 215), (252, 148, 185)]
PINK_HELIX = [(255, 198, 222), (255, 212, 232), (255, 182, 212)]
PINK_GROUND = [(255, 170, 200), (255, 152, 190), (252, 142, 182)]
GIFT_COLORS = [(255, 110, 145), (255, 195, 120), (255, 218, 232), (255, 140, 172)]


def rnd(a, b):
    return random.uniform(a, b)


class P:
    """3D 粒子"""
    __slots__ = ("x", "y", "z", "size", "color", "bright", "tw", "twp")

    def __init__(self, x, y, z, size, color, bright, tw=0.0, twp=0.0):
        self.x, self.y, self.z = x, y, z
        self.size = size
        self.color = color
        self.bright = bright
        self.tw = tw
        self.twp = twp


def make_cloud():
    """树体：锥体内雾状粒子云（越靠边缘越密，营造绒感）"""
    pts = []
    for _ in range(N_CLOUD):
        t = random.random() ** 0.9
        y = t * TREE_HEIGHT
        r = TREE_BASE_RADIUS * (1.0 - t) * (rnd(0.15, 1.0) ** 0.65)
        ang = random.uniform(0, math.tau)
        jitter = rnd(0.9, 1.12)
        pts.append(P(r * jitter * math.cos(ang), y + rnd(-0.05, 0.05),
                     r * jitter * math.sin(ang),
                     size=rnd(0.9, 2.0),
                     color=random.choice(PINK_CLOUD),
                     bright=rnd(0.55, 1.0),
                     tw=rnd(1.2, 3.0), twp=random.uniform(0, math.tau)))
    return pts


def make_helix():
    """螺旋彩带：从树底绕到树顶的亮色粒子带（旋转时的视觉焦点）"""
    pts = []
    turns = 3.4
    for _ in range(N_HELIX):
        t = rnd(0.03, 1.0)
        y = t * TREE_HEIGHT
        ang = t * turns * math.tau
        r = TREE_BASE_RADIUS * (1.0 - t) + 0.10
        # 在带子上做小高斯散布，形成柔和"缎带"厚度
        dr = random.gauss(0, 0.038)
        dy = random.gauss(0, 0.03)
        da = random.gauss(0, 0.03)
        a = ang + da
        rr = (r + dr)
        pts.append(P(rr * math.cos(a), y + dy, rr * math.sin(a),
                     size=rnd(1.2, 2.3),
                     color=random.choice(PINK_HELIX),
                     bright=rnd(1.0, 1.3),
                     tw=rnd(1.5, 3.2), twp=random.uniform(0, math.tau)))
    return pts


def make_ground():
    """底部裙摆：椭圆散布的粒子地面，向边缘渐稀渐淡"""
    pts = []
    for _ in range(N_GROUND):
        r = GROUND_RADIUS * (random.random() ** 0.55)
        ang = random.uniform(0, math.tau)
        pts.append(P(r * math.cos(ang), rnd(-0.22, 0.02), r * math.sin(ang) * 1.0,
                     size=rnd(0.7, 1.7),
                     color=random.choice(PINK_GROUND),
                     bright=max(0.15, 1.0 - r / GROUND_RADIUS) * rnd(0.6, 1.0),
                     tw=rnd(1.0, 2.5), twp=random.uniform(0, math.tau)))
    return pts


def make_baubles():
    """圣诞球挂饰：锥面上的高亮点（白粉色，明显大于普通粒子）"""
    pts = []
    for _ in range(N_BAUBLE):
        t = rnd(0.08, 0.9)
        y = t * TREE_HEIGHT
        r = TREE_BASE_RADIUS * (1.0 - t)
        ang = random.uniform(0, math.tau)
        c = random.choice([(255, 235, 242), (255, 190, 215), (255, 210, 170)])
        pts.append(P(r * math.cos(ang), y, r * math.sin(ang),
                     size=rnd(2.6, 3.6), color=c,
                     bright=1.15, tw=rnd(1.8, 3.6), twp=random.uniform(0, math.tau)))
    return pts


def make_gifts():
    """礼物盒：树底四周几个粒子线框立方体（随场景一起旋转）"""
    gifts = []
    specs = [
        # (x, z, size, 朝向角, 主色, 丝带色)
        (-1.55, 0.9, 0.34, 0.4, GIFT_COLORS[0], (255, 235, 240)),
        (1.5, 1.1, 0.28, -0.5, GIFT_COLORS[1], (255, 240, 245)),
        (0.6, 1.9, 0.24, 0.9, GIFT_COLORS[2], GIFT_COLORS[0]),
        (-0.7, 2.0, 0.20, -1.1, GIFT_COLORS[3], (255, 230, 238)),
    ]
    for gx, gz, s, ry, c_main, c_ribbon in specs:
        pts = []
        corners = [(sx, sy, sz) for sx in (-1, 1) for sy in (0, 2) for sz in (-1, 1)]
        edges = []
        for i, a in enumerate(corners):
            for b in corners[i + 1:]:
                diff = sum(1 for u, v in zip(a, b) if u != v)
                if diff == 1:
                    edges.append((a, b))
        cosr, sinr = math.cos(ry), math.sin(ry)
        for (a, b) in edges:
            for k in range(N_GIFT_EDGE):
                u = k / (N_GIFT_EDGE - 1)
                px = a[0] + (b[0] - a[0]) * u
                py = a[1] + (b[1] - a[1]) * u
                pz = a[2] + (b[2] - a[2]) * u
                X, Y, Z = px * s, py * s * 0.9, pz * s
                x = X * cosr - Z * sinr
                z = X * sinr + Z * cosr
                # 丝带：顶部四条棱 + 交叉竖棱用丝带色
                is_ribbon = py > 1.99 or (abs(abs(px) - 1) < 0.01 and abs(px) != abs(pz))
                c = c_ribbon if is_ribbon else c_main
                pts.append(P(gx + x + rnd(-0.012, 0.012), Y + rnd(-0.012, 0.012),
                             gz + z + rnd(-0.012, 0.012),
                             size=rnd(1.3, 2.0), color=c,
                             bright=rnd(0.9, 1.2),
                             tw=rnd(1.5, 3.0), twp=random.uniform(0, math.tau)))
        gifts.append(pts)
    return gifts


def make_stars():
    """背景星空：白色小星星，缓慢闪烁"""
    stars = []
    for _ in range(N_STARS):
        stars.append({
            "x": random.uniform(0, WIDTH), "y": random.uniform(0, HEIGHT),
            "size": random.choice((1, 1, 1, 2)),
            "base": rnd(90, 200),
            "tw": rnd(0.8, 2.5), "twp": random.uniform(0, math.tau),
        })
    return stars


class Snow:
    def __init__(self):
        self.reset(first=True)

    def reset(self, first=False):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(-HEIGHT, HEIGHT) if first else -10
        self.speed = rnd(28, 85)
        self.drift = rnd(-14, 14)
        self.size = random.choice((1, 1, 2, 2, 3))

    def step(self, dt):
        self.y += self.speed * dt
        self.x += self.drift * dt
        if self.y > HEIGHT + 10:
            self.reset()

    def draw(self, surf):
        c = (235, 238, 245)
        pygame.draw.circle(surf, c, (int(self.x), int(self.y)), self.size)


def heart_points(n, scale=0.034):
    pts = []
    for i in range(n):
        t = (i / n) * math.tau
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x * scale, y * scale))
    return pts


def make_heart():
    """树顶立体爱心：以爱心轮廓为截面，按离边缘比例向外鼓出厚度（中间厚、边缘薄），
    生成真正的 3D 粒子体，跟随场景一起旋转。"""
    scale = 0.044
    poly = heart_points(400, scale)          # 闭合轮廓多边形（XY 平面）

    def inside(px, py):
        """射线法判断点是否在爱心多边形内"""
        hit = False
        j = len(poly) - 1
        for i in range(len(poly)):
            xi, yi = poly[i]
            xj, yj = poly[j]
            if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
                hit = not hit
            j = i
        return hit

    def boundary_ratio(px, py):
        """p 点沿原点方向到轮廓的距离比例 s∈(0,1]：
        p 在缩放 s 的爱心内 ⇔ p/s 在原爱心内。二分求最小 s。"""
        lo, hi = 0.02, 1.0
        # p 本身在内部（hi=1 成立），逐步缩小直到不成立
        for _ in range(18):
            mid = (lo + hi) / 2
            if inside(px / mid, py / mid):
                hi = mid
            else:
                lo = mid
        return hi

    pts = []
    # 轮廓：两圈错位粒子（略带 z 厚度，让侧面转过来也有轮廓）
    for ring in (heart_points(400, scale), heart_points(400, scale * 0.94)):
        for i in range(0, len(ring), 2):
            hx, hy = ring[i]
            pts.append(P(hx + random.gauss(0, 0.006), hy + random.gauss(0, 0.006),
                         rnd(-0.05, 0.05),
                         size=random.choice((1.9, 2.3, 2.7)), color=(255, 138, 176),
                         bright=rnd(1.1, 1.35),
                         tw=rnd(1.5, 3.0), twp=random.uniform(0, math.tau)))

    # 内部体积填充：网格 + 抖动，厚度 = T * sqrt(1 - s²)（s 为到边缘的比例）
    THICK = 0.52
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    step = 0.030
    y = min(ys) + step * 0.5
    while y < max(ys):
        x = min(xs) + step * 0.5
        while x < max(xs):
            jx = x + random.gauss(0, step * 0.25)
            jy = y + random.gauss(0, step * 0.25)
            if inside(jx, jy):
                s = boundary_ratio(jx, jy)
                half = THICK * math.sqrt(max(0.0, 1.0 - s * s))
                # 厚度方向撒 2~3 层粒子
                n_layers = max(1, int(half / 0.07) + 1)
                for _ in range(n_layers):
                    z = rnd(-half, half)
                    shade = 0.8 + 0.35 * (z / THICK if THICK else 0)   # 正面亮、背面暗
                    pts.append(P(jx + rnd(-0.008, 0.008), jy + rnd(-0.008, 0.008), z,
                                 size=random.choice((1.3, 1.7, 2.1)),
                                 color=random.choice([(255, 158, 194), (255, 170, 202), (255, 146, 184)]),
                                 bright=rnd(0.9, 1.2) * shade,
                                 tw=rnd(1.5, 3.0), twp=random.uniform(0, math.tau)))
            x += step
        y += step
    return pts


# ---------------- 场景与渲染 ----------------
class Scene:
    def __init__(self):
        self.cloud = make_cloud()
        self.helix = make_helix()
        self.ground = make_ground()
        self.baubles = make_baubles()
        self.gifts = make_gifts()
        self.heart = make_heart()
        self.stars = make_stars()
        self.snow = [Snow() for _ in range(N_SNOW)]
        self.rot_y = 0.0
        self.tilt = 0.10
        self.auto_rotate = True
        self.drag_active = False
        self.last_mouse = (0, 0)
        self.time_now = 0.0
        self.cx = WIDTH // 2
        self.cy_base = int(HEIGHT * 0.88)
        self.scale = 88.0
        self.cam_dist = 8.0
        self.heart_world_y = TREE_HEIGHT + 0.45
        self.font = pygame.font.SysFont("arial", 30, bold=True)
        self._text_cache = None

    def project(self, p):
        cosr, sinr = math.cos(self.rot_y), math.sin(self.rot_y)
        x = p.x * cosr - p.z * sinr
        z = p.x * sinr + p.z * cosr
        y = p.y
        cost, sint = math.cos(self.tilt), math.sin(self.tilt)
        y2 = y * cost - z * sint
        z2 = y * sint + z * cost
        depth = self.cam_dist + z2
        if depth < 0.5:
            depth = 0.5
        f = self.scale * self.cam_dist / depth
        return self.cx + x * f, self.cy_base - y2 * f, depth, f

    def _draw_3d_list(self, screen, particles, boost=1.0):
        batch = []
        for p in particles:
            sx, sy, depth, f = self.project(p)
            near = max(0.0, min(1.0, (self.cam_dist + 3.4 - depth) / 4.2))
            b = (0.62 + 0.9 * near) * p.bright * boost
            if p.tw:
                b *= 0.72 + 0.28 * math.sin(self.time_now * p.tw + p.twp)
            b = max(0.0, min(1.6, b))
            c = p.color
            col = (min(255, int(c[0] * b)), min(255, int(c[1] * b)), min(255, int(c[2] * b)))
            size = max(1, int(p.size * (0.75 + 0.5 * near)))
            batch.append((depth, sx, sy, size, col, p.size))
        batch.sort(key=lambda e: e[0], reverse=True)
        for depth, sx, sy, size, col, base in batch:
            pygame.draw.circle(screen, col, (int(sx), int(sy)), size)
            if base >= 2.4:
                halo = (col[0] // 4 + 26, col[1] // 4 + 18, col[2] // 4 + 26)
                pygame.draw.circle(screen, halo, (int(sx), int(sy)), size + 2)

    def draw_text(self, screen):
        if self._text_cache is None:
            base = self.font.render("Merry Christmas", True, (255, 210, 225))
            glow = pygame.Surface(base.get_size(), pygame.SRCALPHA)
            for dx in (-2, -1, 0, 1, 2):
                for dy in (-2, -1, 0, 1, 2):
                    if dx or dy:
                        glow.blit(base, (dx, dy))
            glow.set_alpha(45)
            img = pygame.Surface(base.get_size(), pygame.SRCALPHA)
            img.blit(glow, (0, 0))
            img.blit(base, (0, 0))
            self._text_cache = img
        screen.blit(self._text_cache, (28, 26))

    def draw(self, screen, dt):
        self.time_now += dt
        if self.auto_rotate and not self.drag_active:
            self.rot_y += AUTO_ROTATE_SPEED * dt
        t = self.time_now

        screen.fill(BG_COLOR)

        # 星空（缓慢闪烁）
        for s in self.stars:
            b = s["base"] * (0.65 + 0.35 * math.sin(t * s["tw"] + s["twp"]))
            col = (int(b), int(b * 0.98), min(255, int(b * 1.05)))
            pygame.draw.circle(screen, col, (int(s["x"]), int(s["y"])), s["size"])

        # 十字星光芒（偶尔闪现）
        for i in range(0, N_STARS, 23):
            s = self.stars[i]
            if math.sin(t * 1.3 + s["twp"]) > 0.9:
                x, y = int(s["x"]), int(s["y"])
                pygame.draw.line(screen, (240, 242, 250), (x - 5, y), (x + 5, y), 1)
                pygame.draw.line(screen, (240, 242, 250), (x, y - 5), (x, y + 5), 1)

        # 3D 粒子（由远及近：地面 -> 树体 -> 螺旋 -> 挂饰 -> 礼物）
        self._draw_3d_list(screen, self.ground, boost=1.0)
        self._draw_3d_list(screen, self.cloud)
        self._draw_3d_list(screen, self.helix, boost=1.1)
        self._draw_3d_list(screen, self.baubles, boost=1.15)
        for gift in self.gifts:
            self._draw_3d_list(screen, gift, boost=1.25)

        # 树顶立体爱心（3D 粒子体，跟随场景一起旋转 + 心跳脉动）
        heartbeat = 1.0 + 0.10 * math.sin(t * 2.6)
        hb = [P(p.x * heartbeat,
                p.y * heartbeat + self.heart_world_y,
                p.z * heartbeat,
                p.size, p.color, p.bright, p.tw, p.twp)
              for p in self.heart]
        self._draw_3d_list(screen, hb, boost=1.15)

        # 飘雪
        for s in self.snow:
            s.step(dt)
            s.draw(screen)

        self.draw_text(screen)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("粉色粒子螺旋圣诞树 · Merry Christmas")
    clock = pygame.time.Clock()
    scene = Scene()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_SPACE:
                    scene.auto_rotate = not scene.auto_rotate
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                scene.drag_active = True
                scene.last_mouse = ev.pos
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                scene.drag_active = False
            elif ev.type == pygame.MOUSEMOTION and scene.drag_active:
                dx, dy = ev.pos[0] - scene.last_mouse[0], ev.pos[1] - scene.last_mouse[1]
                scene.rot_y += dx * 0.008
                scene.tilt = max(-0.45, min(0.7, scene.tilt + dy * 0.004))
                scene.last_mouse = ev.pos
        scene.draw(screen, dt)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
