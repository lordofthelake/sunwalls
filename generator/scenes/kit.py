"""Flat, detailed building kit. All sizes in vertical (H) units; U() converts to x units.
Two flat tones per structure (sc body, sc2 accents) + window colour wc (dark-ish by day, warm at night)."""
from themes3 import R, U, rgba

class Kit:
    def __init__(self, d, Pp, sc, sc2, wc, lights=None, warm=None, lit=0.):
        self.d, self.P, self.sc, self.sc2, self.wc = d, Pp, sc, sc2, wc
        self.lights = lights if lights is not None else []; self.warm = warm; self.lit = lit

    def rect(self, x0, y0, x1, y1, c=None): self.d.rectangle(R(self.P, x0, y0, x1, y1), fill=rgba(self.sc if c is None else c, 1))
    def poly(self, pts, c=None): self.d.polygon([self.P(x, y) for x, y in pts], fill=rgba(self.sc if c is None else c, 1))
    def half(self, x, y, rx, ry, c=None): self.d.pieslice(R(self.P, x - U(rx), y - ry, x + U(rx), y + ry), 180, 360, fill=rgba(self.sc if c is None else c, 1))
    def oval(self, x, y, rx, ry, c=None): self.d.ellipse(R(self.P, x - U(rx), y - ry, x + U(rx), y + ry), fill=rgba(self.sc if c is None else c, 1))
    def win(self, x, y, w, h):
        self.rect(x - U(w / 2), y - h / 2, x + U(w / 2), y + h / 2, self.wc)
        if self.lit > .05: self.lights.append((x, y, 1.2, self.warm, self.lit * .05))

    def dome(self, x, g, r, windows=True):
        self.rect(x - U(r * 1.08), g - r * .18, x + U(r * 1.08), g + .03)               # plinth
        self.half(x, g - r * .18, r, r)                                                 # shell
        self.half(x, g - r * .18 - r * .42, r * .58, r * .58, self.sc2)                 # cap band
        self.half(x, g - r * .18 - r * .42, r * .38, r * .38)                           # crown
        self.rect(x - U(r * .1), g - r * 1.32, x + U(r * .1), g - r * 1.12)             # lantern
        self.half(x, g - r * 1.32, r * .16, r * .12, self.sc2)
        if windows:
            for q in (-.62, -.31, 0, .31, .62): self.win(x + U(r * q), g - r * .5, r * .1, r * .09)
            self.half(x, g + .002, r * .16, r * .2, self.wc)                           # door arch

    def tower(self, x, g, ht, w):
        self.rect(x - U(w), g - ht * .32, x + U(w), g + .03)                             # base block
        self.rect(x - U(w * 1.25), g - ht * .34, x + U(w * 1.25), g - ht * .3, self.sc2)
        self.rect(x - U(w * .62), g - ht * .78, x + U(w * .62), g - ht * .32)            # shaft
        self.rect(x - U(w * .32), g - ht, x + U(w * .32), g - ht * .78)                  # needle
        self.oval(x, g - ht * .58, w * 2.0, ht * .028, self.sc2)                         # platforms
        self.oval(x, g - ht * .58 + ht * .02, w * 1.3, ht * .02)
        self.oval(x, g - ht * .84, w * 1.1, ht * .02, self.sc2)
        self.oval(x, g - ht * 1.01, w * .6, ht * .03)
        for j in range(4): self.win(x, g - ht * (.08 + j * .065), w * .45, ht * .028)
        for j in range(3): self.win(x, g - ht * (.4 + j * .07), w * .35, ht * .025)
        self.lights.append((x, g - ht * 1.02, 2.4, '#ff9a8a', self.lit * .4 + .05))

    def block(self, x, g, w, hgt, rows=2, cols=3, roof=True):
        self.rect(x - U(w / 2), g - hgt, x + U(w / 2), g + .03)
        self.rect(x - U(w / 2 * 1.06), g - hgt - .003, x + U(w / 2 * 1.06), g - hgt + .002, self.sc2)
        if roof: self.rect(x - U(w * .18), g - hgt - .009, x + U(w * .05), g - hgt)
        for r in range(rows):
            for c in range(cols):
                self.win(x + U(w * ((c + .5) / cols - .5) * .8), g - hgt * (.3 + r * .55 / max(rows - 1, 1) * .9 if rows > 1 else .5), w * .12, hgt * .14)

    def ziggurat(self, x, g, w, steps=3, sh=.009):
        for s in range(steps):
            ww = w * (1 - s * .26); c = self.sc if s % 2 == 0 else self.sc2
            self.rect(x - U(ww / 2), g - sh * (s + 1), x + U(ww / 2), g - sh * s + (.03 if s == 0 else 0), c)
        self.win(x, g - sh * .5, w * .1, sh * .5)

    def tube(self, x0, x1, y0, y1, sag=.01, th=.0045):
        """thick walkway tube arcing between two points"""
        pts = []
        for i in range(25):
            t = i / 24; x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t) * -1
            pts.append(self.P(x, y))
        self.d.line(pts, fill=rgba(self.sc, 1), width=int(th * (self.P(0, 1)[1] - self.P(0, 0)[1])), joint='curve')

    def dish(self, x, g, r, facing=1):
        """radio dish: tapered pylon, yoke, bowl tilted ~30deg toward the sky; everything on one axis."""
        import math
        self.poly([(x - U(r * .42), g + .03), (x + U(r * .42), g + .03), (x + U(r * .14), g - r * 1.0), (x - U(r * .14), g - r * 1.0)])
        self.rect(x - U(r * .5), g - r * .22, x + U(r * .5), g - r * .12, self.sc2)
        cx, cy = x, g - r * 1.25                       # bowl hub sits right on top of the pylon
        tilt = math.radians(30) * facing               # axis tilted from vertical
        ax, ay = math.sin(tilt), -math.cos(tilt)       # axis direction (up, leaning toward facing)
        px_, py_ = math.cos(tilt), math.sin(tilt)      # rim direction
        def P_(t, back=0.):                            # point on the parabola (back>0 = shell underside)
            u = r * t; v = r * .45 * t * t - back * r * (1 - t * t)
            return (cx + U(px_ * u + ax * v), cy + py_ * u + ay * v)
        ts = [-1 + 2 * i / 30 for i in range(31)]
        face = [P_(t) for t in ts]
        self.poly(face, self.sc2)                                              # bowl face (lens)
        self.poly(face + [P_(t, .16) for t in reversed(ts)])                  # solid shell behind it
        fx, fy = cx + U(ax * r * .95), cy + ay * r * .95
        th = max(3, int(r * .09 * (self.P(0, 1)[1] - self.P(0, 0)[1])))
        for e in (-1, 1):                                                      # feed struts from the rim
            ex, ey = cx + U(px_ * r * e + ax * r * .45), cy + py_ * r * e + ay * r * .45
            self.d.line([self.P(ex, ey), self.P(fx, fy)], fill=rgba(self.sc, 1), width=th)
        self.oval(fx, fy, r * .09, r * .09)
        self.oval(cx, cy, r * .16, r * .16)

    def observatory(self, x, g, r):
        """drum + dome with a centred observing slit + small annexes, all symmetric about x."""
        self.rect(x - U(r * 1.1), g - r * .5, x + U(r * 1.1), g + .03)
        self.rect(x - U(r * 1.2), g - r * .56, x + U(r * 1.2), g - r * .48, self.sc2)
        self.half(x, g - r * .56, r, r)
        self.poly([(x - U(r * .14), g - r * 1.5), (x + U(r * .14), g - r * 1.5), (x + U(r * .2), g - r * .7), (x - U(r * .2), g - r * .7)], self.sc2)
        for q in (-.7, -.35, .35, .7): self.win(x + U(r * q), g - r * .25, r * .1, r * .1)
        self.rect(x - U(r * 1.8), g - r * .28, x - U(r * 1.1), g + .03)
        self.rect(x + U(r * 1.1), g - r * .28, x + U(r * 1.8), g + .03)

    def cabin(self, x, g, w, hgt):
        self.rect(x - U(w / 2), g - hgt, x + U(w / 2), g + .03)
        self.poly([(x - U(w * .62), g - hgt + .002), (x, g - hgt - w * .45), (x + U(w * .62), g - hgt + .002)], self.sc2)
        self.rect(x + U(w * .18), g - hgt - w * .42, x + U(w * .3), g - hgt - w * .1)       # chimney
        self.win(x - U(w * .2), g - hgt * .5, w * .18, hgt * .3)
        self.win(x + U(w * .2), g - hgt * .5, w * .18, hgt * .3)

    def lighthouse(self, x, g, ht, w):
        self.poly([(x - U(w), g + .03), (x + U(w), g + .03), (x + U(w * .62), g - ht), (x - U(w * .62), g - ht)])
        for f in (.3, .6): self.rect(x - U(w * (1 - f * .4)), g - ht * f - .004, x + U(w * (1 - f * .4)), g - ht * f + .002, self.sc2)
        self.rect(x - U(w * .95), g - ht - .006, x + U(w * .95), g - ht)                   # gallery
        self.rect(x - U(w * .55), g - ht - .022, x + U(w * .55), g - ht - .006, self.wc)   # lantern room
        self.half(x, g - ht - .022, w * .62, .012)
        self.rect(x - U(w * .1), g - ht - .042, x + U(w * .1), g - ht - .03)
        for f in (.15, .45, .75): self.win(x, g - ht * f, w * .22, .006)

def _kit_extras():
    import math
    def turbine(self, x, g, ht, phase=0.):
        """wind turbine: tapered mast, nacelle, three wide blades"""
        self.poly([(x - U(ht * .035), g + .03), (x + U(ht * .035), g + .03), (x + U(ht * .015), g - ht), (x - U(ht * .015), g - ht)])
        hx, hy = x, g - ht
        for j in range(3):
            a = phase + j * 2 * math.pi / 3; L = ht * .5; w = ht * .07
            dx, dy = math.cos(a), math.sin(a); nx, ny = -dy, dx
            self.poly([(hx + U(nx * w), hy + ny * w), (hx + U(dx * L), hy + dy * L), (hx - U(nx * w * .4), hy - ny * w * .4)], self.sc2 if j == 0 else None)
        self.oval(hx, hy, ht * .05, ht * .05)

    def greenhouse(self, x, g, w, hgt, ribs=4):
        """long vaulted greenhouse: flat glowing panes between solid ribs"""
        self.rect(x - U(w / 2), g - hgt * .35, x + U(w / 2), g + .03)
        self.d.chord(R(self.P, x - U(w / 2), g - hgt * 1.35, x + U(w / 2), g + hgt * .65), 180, 360, fill=rgba(self.wc, 1))
        for j in range(ribs + 1):
            xx = x - U(w / 2) + U(w) * j / ribs
            self.rect(xx - U(w * .025), g - hgt * (1 - abs(j / ribs - .5) * 1.1), xx + U(w * .025), g, self.sc)
        self.rect(x - U(w / 2), g - hgt * .4, x + U(w / 2), g - hgt * .3, self.sc)

    def hangar(self, x, g, w, hgt):
        """arched hangar with a big door and a side annex"""
        self.d.chord(R(self.P, x - U(w / 2), g - hgt, x + U(w / 2), g + hgt), 180, 360, fill=rgba(self.sc, 1))
        self.rect(x - U(w / 2), g - .002, x + U(w / 2), g + .03)
        self.d.chord(R(self.P, x - U(w * .3), g - hgt * .62, x + U(w * .3), g + hgt * .62), 180, 360, fill=rgba(self.wc, 1))
        for j in (-.15, 0, .15): self.rect(x + U(w * j) - U(w * .012), g - hgt * .6, x + U(w * j) + U(w * .012), g, self.sc)
        self.rect(x + U(w * .5), g - hgt * .45, x + U(w * .72), g + .03, self.sc2)

    def control_tower(self, x, g, ht, w):
        """shaft with a flared cab of windows on top"""
        self.rect(x - U(w * .5), g - ht * .8, x + U(w * .5), g + .03)
        self.poly([(x - U(w * .5), g - ht * .8), (x + U(w * .5), g - ht * .8), (x + U(w * 1.3), g - ht * .9), (x - U(w * 1.3), g - ht * .9)])
        self.rect(x - U(w * 1.3), g - ht, x + U(w * 1.3), g - ht * .9, self.wc)
        for j in (-.8, 0, .8): self.rect(x + U(w * j) - U(w * .12), g - ht, x + U(w * j) + U(w * .12), g - ht * .9)
        self.rect(x - U(w * 1.45), g - ht * 1.04, x + U(w * 1.45), g - ht)
        self.rect(x - U(w * .12), g - ht * 1.2, x + U(w * .12), g - ht * 1.04)
        self.lights.append((x, g - ht * 1.2, 2.2, '#ff9a8a', self.lit * .4 + .05))

    def tanks(self, x, g, r, n=3):
        """row of upright fuel tanks with rounded caps and a shared pipe band"""
        for j in range(n):
            xx = x + U(r * 2.3 * (j - (n - 1) / 2))
            self.rect(xx - U(r), g - r * 2.2, xx + U(r), g + .03)
            self.half(xx, g - r * 2.2, r, r * .7)
            self.rect(xx - U(r), g - r * 1.3, xx + U(r), g - r * 1.1, self.sc2)
        self.rect(x - U(r * 2.3 * (n - 1) / 2), g - r * .7, x + U(r * 2.3 * (n - 1) / 2), g - r * .45)

    for f in (turbine, greenhouse, hangar, control_tower, tanks): setattr(Kit, f.__name__, f)
_kit_extras()
