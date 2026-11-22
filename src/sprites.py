"""Personnages et décors dessinés en code : Roux le renard, Pico le hérisson.
Tout est original et libre de droits. Chaque sprite est dessiné en grand (S x)
puis réduit pour des bords lisses."""
import math
import random
from PIL import Image, ImageDraw, ImageChops

S = 3

ORANGE = (232, 116, 42, 255)
ORANGE_D = (190, 84, 26, 255)
CREAM = (255, 241, 215, 255)
DARK = (58, 36, 24, 255)
WHITE = (255, 255, 255, 255)
TAN = (214, 170, 120, 255)
TAN_L = (240, 214, 172, 255)
SPIKE = (86, 58, 42, 255)
SPIKE_L = (122, 86, 62, 255)
RED = (217, 58, 43, 255)
PINK = (244, 120, 140, 255)


class Cv:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def ell(self, cx, cy, rx, ry, fill, outline=None, width=0):
        self.d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S],
                       fill=fill, outline=outline, width=int(width * S))

    def poly(self, pts, fill):
        self.d.polygon([(x * S, y * S) for x, y in pts], fill=fill)

    def line(self, pts, fill, width):
        self.d.line([(x * S, y * S) for x, y in pts], fill=fill, width=int(width * S), joint="curve")
        r = width / 2
        for x, y in (pts[0], pts[-1]):
            self.ell(x, y, r, r, fill)

    def arc(self, box, a0, a1, fill, width):
        x0, y0, x1, y1 = box
        self.d.arc([x0 * S, y0 * S, x1 * S, y1 * S], a0, a1, fill=fill, width=int(width * S))

    def rrect(self, box, r, fill):
        x0, y0, x1, y1 = box
        self.d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=r * S, fill=fill)

    def done(self):
        return self.im.resize((self.w, self.h), Image.LANCZOS)


def paste_rot(cv, layer, cx, cy, angle):
    """Colle `layer` (image à l'échelle S) tourné de `angle` degrés, centré en (cx, cy)."""
    r = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    x = int(cx * S - r.width / 2)
    y = int(cy * S - r.height / 2)
    cv.im.alpha_composite(r, dest=(max(x, 0), max(y, 0)))


# ---------- visages ----------
def eyes(c, centers, kind, lid_color, r=1.0):
    for i, (ex, ey) in enumerate(centers):
        side = -1 if i == 0 else 1
        if kind == "happy":
            c.arc((ex - 22 * r, ey - 14 * r, ex + 22 * r, ey + 18 * r), 200, 340, DARK, 7)
            continue
        rx, ry = 24 * r, 28 * r
        pr = 12 * r
        if kind == "surprised":
            rx, ry, pr = 28 * r, 34 * r, 8 * r
        c.ell(ex, ey, rx, ry, WHITE, outline=DARK, width=3)
        c.ell(ex, ey + 3 * r, pr, pr * 1.2, DARK)
        c.ell(ex + 4 * r, ey - 3 * r, 4 * r, 4 * r, WHITE)
        if kind == "greedy":
            c.poly([(ex - rx - 3, ey - ry - 3), (ex + rx + 3, ey - ry - 3),
                    (ex + rx + 3, ey - 10), (ex - rx - 3, ey - 10)], lid_color)
            c.line([(ex - rx, ey - 10), (ex + rx, ey - 10)], DARK, 5)
        if kind in ("sad", "worried"):
            inner = ex - side * 24 * r
            outer = ex + side * 24 * r
            # sourcil : le bout intérieur est plus haut
            c.line([(outer, ey - 30 * r), (-side * -1 * 0 + ex - side * 22 * r, ey - 46 * r)], DARK, 6)
            if kind == "sad":
                c.ell(ex + side * 6 * r, ey + 38 * r, 6 * r, 9 * r, (120, 190, 240, 255))


def mouth(c, cx, cy, kind):
    if kind == "smile":
        c.arc((cx - 30, cy - 18, cx + 30, cy + 20), 15, 165, DARK, 6)
    elif kind == "frown":
        c.arc((cx - 24, cy + 2, cx + 24, cy + 34), 200, 340, DARK, 6)
    elif kind == "smirk":
        c.line([(cx - 24, cy + 8), (cx + 24, cy - 6)], DARK, 6)
    elif kind == "open":
        c.ell(cx, cy + 8, 20, 17, DARK)
        c.ell(cx, cy + 16, 11, 7, (240, 110, 120, 255))
    elif kind == "oh":
        c.ell(cx, cy + 8, 10, 13, DARK)


EXPR = {
    "neutral": ("neutral", "smile"),
    "smile": ("neutral", "smile"),
    "greedy": ("greedy", "smirk"),
    "sad": ("sad", "frown"),
    "worried": ("worried", "frown"),
    "surprised": ("surprised", "oh"),
    "happy": ("happy", "open"),
}


# ---------- Roux le renard : toile 520 x 580, pieds en bas ----------
def fox(expr="neutral"):
    c = Cv(520, 580)
    # queue
    tail = Cv(240, 140)
    tail.ell(120, 70, 112, 56, ORANGE)
    base_alpha = tail.im.getchannel("A")
    tip = Image.new("RGBA", tail.im.size, (0, 0, 0, 0))
    ImageDraw.Draw(tip).ellipse([150 * S, 6 * S, 235 * S, 134 * S], fill=CREAM)
    tip.putalpha(ImageChops.multiply(tip.getchannel("A"), base_alpha))
    tail.im.alpha_composite(tip)
    tail.im = tail.im.transpose(Image.FLIP_LEFT_RIGHT)
    paste_rot(c, tail.im, 135, 420, -38)
    # pieds, corps, bras
    c.ell(205, 548, 46, 24, DARK)
    c.ell(315, 548, 46, 24, DARK)
    c.ell(260, 410, 116, 138, ORANGE)
    c.ell(260, 432, 72, 100, CREAM)
    c.ell(140, 402, 27, 70, ORANGE_D)
    c.ell(380, 402, 27, 70, ORANGE_D)
    c.ell(140, 466, 25, 21, DARK)
    c.ell(380, 466, 25, 21, DARK)
    # oreilles
    c.poly([(138, 165), (150, 40), (226, 118)], ORANGE)
    c.poly([(382, 165), (370, 40), (294, 118)], ORANGE)
    c.poly([(158, 150), (164, 78), (208, 122)], (250, 168, 140, 255))
    c.poly([(362, 150), (356, 78), (312, 122)], (250, 168, 140, 255))
    # tête
    c.ell(260, 215, 130, 108, ORANGE)
    c.ell(196, 268, 74, 56, CREAM)
    c.ell(324, 268, 74, 56, CREAM)
    c.ell(260, 262, 50, 35, CREAM)
    c.ell(260, 243, 18, 13, DARK)
    ek, mk = EXPR[expr]
    eyes(c, [(205, 198), (315, 198)], ek, ORANGE)
    mouth(c, 260, 275, mk)
    return c.done()


# ---------- Pico le hérisson : toile 520 x 440 ----------
def hedgehog(expr="neutral"):
    c = Cv(520, 440)
    # piquants
    c.ell(260, 235, 215, 168, SPIKE)
    for layer, (r1x, r1y, r2x, r2y, col, step) in enumerate([
            (205, 160, 262, 214, SPIKE, 8), (190, 148, 236, 192, SPIKE_L, 12)]):
        a = 180
        while a <= 360:
            def p(angle, rx, ry):
                return (260 + rx * math.cos(math.radians(angle)), 235 + ry * math.sin(math.radians(angle)))
            c.poly([p(a - step / 2, r1x, r1y), p(a, r2x, r2y), p(a + step / 2, r1x, r1y)], col)
            a += step
    c.ell(260, 235, 196, 150, SPIKE_L)
    # pieds et corps
    c.ell(200, 420, 44, 20, (150, 108, 74, 255))
    c.ell(320, 420, 44, 20, (150, 108, 74, 255))
    c.ell(260, 340, 116, 92, TAN)
    c.ell(145, 360, 24, 36, TAN)
    c.ell(375, 360, 24, 36, TAN)
    # tête
    c.ell(146, 218, 28, 28, (180, 132, 96, 255))
    c.ell(374, 218, 28, 28, (180, 132, 96, 255))
    c.ell(260, 285, 128, 102, TAN)
    c.ell(260, 312, 90, 68, TAN_L)
    c.ell(260, 328, 58, 40, (250, 226, 196, 255))
    c.ell(260, 310, 19, 14, DARK)
    ek, mk = EXPR[expr]
    eyes(c, [(205, 262), (315, 262)], ek, TAN, r=0.95)
    mouth(c, 260, 342, mk)
    return c.done()


# ---------- objets ----------
def apple():
    c = Cv(110, 120)
    c.ell(55, 70, 44, 42, RED)
    c.ell(36, 58, 10, 14, (240, 120, 100, 255))
    c.line([(55, 32), (60, 12)], (110, 70, 40, 255), 6)
    leaf = Cv(60, 36)
    leaf.ell(30, 18, 28, 12, (92, 170, 70, 255))
    paste_rot(c, leaf.im, 82, 22, -25)
    return c.done()


def basket_parts():
    back = Cv(280, 190)
    back.ell(140, 50, 118, 30, (120, 76, 36, 255))
    front = Cv(280, 190)
    front.poly([(26, 52), (254, 52), (226, 176), (54, 176)], (186, 124, 62, 255))
    for i in range(1, 6):
        x = 26 + i * 38
        front.line([(x, 54), (x + (140 - x) * 0.2 * 0 + (-(x - 140) * 0.12), 172)], (140, 92, 44, 255), 4)
    for y in (88, 124, 158):
        front.line([(40, y), (240, y)], (140, 92, 44, 255), 4)
    front.arc((22, 24, 258, 80), 0, 180, (150, 100, 48, 255), 12)
    front.ell(140, 52, 118, 6, (150, 100, 48, 255))
    return back.done(), front.done()


def heart():
    c = Cv(100, 90)
    c.ell(32, 30, 26, 26, PINK)
    c.ell(68, 30, 26, 26, PINK)
    c.poly([(8, 42), (92, 42), (50, 86)], PINK)
    return c.done()


def sparkle():
    c = Cv(80, 80)
    pts = []
    for i in range(8):
        a = math.pi / 4 * i
        r = 38 if i % 2 == 0 else 9
        pts.append((40 + r * math.cos(a), 40 + r * math.sin(a)))
    c.poly(pts, (255, 214, 64, 255))
    return c.done()


def sweat():
    c = Cv(40, 56)
    c.poly([(20, 2), (36, 34), (4, 34)], (120, 190, 240, 255))
    c.ell(20, 36, 16, 16, (120, 190, 240, 255))
    return c.done()


def bubble(w=300, h=240):
    c = Cv(w, h)
    c.rrect((4, 4, w - 4, h - 64), 44, (0, 0, 0, 40))
    c.rrect((0, 0, w - 8, h - 68), 44, WHITE)
    c.poly([(w * 0.28, h - 70), (w * 0.2, h - 8), (w * 0.46, h - 70)], WHITE)
    return c.done()


def red_cross(size=150):
    c = Cv(size, size)
    c.line([(18, 18), (size - 18, size - 18)], (214, 40, 40, 255), 16)
    c.line([(size - 18, 18), (18, size - 18)], (214, 40, 40, 255), 16)
    return c.done()


def bird(flap):
    c = Cv(90, 50)
    y = 12 if flap else 36
    c.line([(6, y), (30, 26), (45, 28)], (60, 50, 70, 255), 5)
    c.line([(84, y), (60, 26), (45, 28)], (60, 50, 70, 255), 5)
    return c.done()


def cloud(w=380, h=170):
    c = Cv(w, h)
    for cx, cy, r in [(90, 100, 54), (160, 76, 66), (236, 94, 58), (300, 108, 44), (200, 114, 52)]:
        c.ell(cx, cy, r, r * 0.8, (255, 255, 255, 235))
    return c.done()


# ---------- décor ----------
def background(w=1080, h=1920, horizon=1260):
    k = 2
    im = Image.new("RGB", (w * k, h * k))
    d = ImageDraw.Draw(im)
    top, bot = (122, 204, 244), (236, 248, 255)
    for y in range(horizon * k):
        t = y / (horizon * k)
        col = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        d.line([(0, y), (w * k, y)], fill=col)
    # soleil
    for r, a in [(190, 40), (150, 70), (110, 120)]:
        glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([(860 - r) * k, (300 - r) * k, (860 + r) * k, (300 + r) * k],
                                    fill=(255, 236, 150, a))
        im.paste(glow, (0, 0), glow)
    d.ellipse([(860 - 78) * k, (300 - 78) * k, (860 + 78) * k, (300 + 78) * k], fill=(255, 226, 90))
    # collines
    d.ellipse([(-300) * k, (1090) * k, 700 * k, 1400 * k], fill=(150, 212, 140))
    d.ellipse([(400) * k, (1120) * k, 1500 * k, 1430 * k], fill=(128, 196, 124))
    # herbe
    g1, g2 = (124, 206, 106), (74, 168, 90)
    for y in range(horizon * k - 40, h * k):
        t = min(1.0, (y - (horizon * k - 40)) / ((h - horizon) * k))
        col = tuple(int(g1[i] + (g2[i] - g1[i]) * t) for i in range(3))
        d.line([(0, y), (w * k, y)], fill=col)
    rnd = random.Random(7)
    for _ in range(120):
        x, y = rnd.randint(0, w), rnd.randint(horizon + 30, 1570)
        s = 6 + (y - horizon) / 80
        col = rnd.choice([(255, 255, 255), (255, 214, 90), (250, 140, 160)])
        d.ellipse([(x - s) * k, (y - s) * k, (x + s) * k, (y + s) * k], fill=col)
    return im.resize((w, h), Image.LANCZOS).convert("RGBA")


def tree_layer(w=1080, h=1920):
    k = 2
    im = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(472 * k, 1400 * k), (608 * k, 1400 * k), (588 * k, 960 * k), (492 * k, 960 * k)], fill=(122, 80, 44))
    for x0, y0, x1, y1 in [(510, 1380, 514, 1040), (560, 1380, 556, 1100), (535, 1370, 540, 980)]:
        d.line([(x0 * k, y0 * k), (x1 * k, y1 * k)], fill=(96, 60, 32), width=8 * k)
    d.ellipse([(430) * k, 1380 * k, 650 * k, 1430 * k], fill=(70, 150, 78))
    leaves = [(540, 640, 240), (370, 770, 175), (710, 770, 175), (440, 520, 160), (640, 520, 160),
              (540, 880, 150), (330, 880, 110), (750, 880, 110)]
    for dark, off in [((52, 140, 70), 22), ((70, 168, 80), 0)]:
        for cx, cy, r in leaves:
            d.ellipse([(cx - r) * k, (cy - r + off) * k, (cx + r) * k, (cy + r + off) * k], fill=dark)
    for cx, cy, r in [(480, 590, 60), (640, 700, 50), (420, 760, 44)]:
        d.ellipse([(cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k], fill=(96, 188, 92))
    return im.resize((w, h), Image.LANCZOS)


APPLE_SPOTS = [(400, 700), (520, 560), (670, 640), (470, 830), (630, 810),
               (350, 840), (740, 790), (545, 705)]
