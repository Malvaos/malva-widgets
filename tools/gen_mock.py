#!/usr/bin/env python3
"""Generate ui/mock.slint: made-up but stable sample data for every widget.

Slint has no loops in expressions, so graph lines are generated here as SVG path strings,
one string per size, for FRAMES successive samples. The app swaps the frame once per
second to make the graphs scroll. Same random generator as the original design boards,
so the numbers match the screenshots.

Run:  python3 tools/gen_mock.py
"""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FRAMES = 8
WARMUP = 68


class Lcg:
    def __init__(self, seed):
        self.s = seed

    def rnd(self):
        self.s = (self.s * 1664525 + 1013904223) % 4294967296
        return self.s / 4294967296


def cl(v, a, b):
    return max(a, min(b, v))


# ---------------------------------------------------------------------------
# series models (ported from the design boards)
# ---------------------------------------------------------------------------
class Cpu:
    def __init__(self):
        self.r = Lcg(11)
        self.t = 20.0
        self.core = [[] for _ in range(16)]
        self.cs = [14.0] * 16
        self.cpu = []

    def step(self):
        r = self.r
        self.t = cl(self.t + (r.rnd() - 0.5) * 7 + (28 * r.rnd() if r.rnd() < 0.05 else 0) - (4 if self.t > 34 else 0), 5, 80)
        # NOTE: JS evaluates `this.rnd() < 0.05 ? 28 * this.rnd() : 0` after the first rnd; same order here.
        total = 0.0
        for i in range(16):
            self.cs[i] = cl(self.cs[i] + (self.t - self.cs[i]) * 0.35 + (r.rnd() - 0.5) * 20, 1, 100)
            total += self.cs[i]
            self.core[i].append(self.cs[i])
            self.core[i] = self.core[i][-60:]
        self.cpu.append(total / 16)
        self.cpu = self.cpu[-60:]


class Memory:
    def __init__(self):
        self.r = Lcg(23)
        self.rr = 50.0
        self.sw = 0.9
        self.ram = []
        self.swap = []

    def step(self):
        r = self.r
        self.rr = cl(self.rr + (r.rnd() - 0.5) * 1.4 + (51 - self.rr) * 0.05, 35, 85)
        self.sw = cl(self.sw + (r.rnd() - 0.5) * 0.06, 0.4, 3)
        self.ram = (self.ram + [self.rr])[-60:]
        self.swap = (self.swap + [self.sw / 8 * 100])[-60:]


class Disk:
    def __init__(self):
        self.r = Lcg(41)
        self.a, self.rd_, self.w = 6.0, 12.0, 5.0
        self.act, self.rd, self.wr = [], [], []

    def step(self):
        r = self.r
        burst = r.rnd() * 40 if r.rnd() < 0.12 else 0
        self.a = cl(self.a + (r.rnd() - 0.5) * 8 + (8 - self.a) * 0.15 + burst * 0.5, 0, 100)
        self.rd_ = cl(self.rd_ + (r.rnd() - 0.5) * 10 + (12 - self.rd_) * 0.12 + burst, 0, 100)
        self.w = cl(self.w + (r.rnd() - 0.5) * 6 + (5 - self.w) * 0.12 + burst * 0.4, 0, 100)
        self.act = (self.act + [self.a])[-60:]
        self.rd = (self.rd + [self.rd_])[-60:]
        self.wr = (self.wr + [self.w])[-60:]


class Network:
    def __init__(self):
        self.r = Lcg(59)
        self.dn, self.up = 28.0, 8.0
        self.dl, self.ul = [], []

    def step(self):
        r = self.r
        burst = r.rnd() * 35 if r.rnd() < 0.1 else 0
        self.dn = cl(self.dn + (r.rnd() - 0.5) * 14 + (26 - self.dn) * 0.1 + burst, 2, 100)
        self.up = cl(self.up + (r.rnd() - 0.5) * 6 + (8 - self.up) * 0.12 + burst * 0.2, 1, 100)
        self.dl = (self.dl + [self.dn])[-60:]
        self.ul = (self.ul + [self.up])[-60:]


class Gpu:
    def __init__(self):
        self.r = Lcg(77)
        self.g, self.v = 22.0, 31.0
        self.gl, self.vl = [], []

    def step(self):
        r = self.r
        self.g = cl(self.g + (r.rnd() - 0.5) * 12 + (24 - self.g) * 0.1, 1, 100)
        self.v = cl(self.v + (r.rnd() - 0.5) * 1.2 + (31 - self.v) * 0.04, 10, 95)
        self.gl = (self.gl + [self.g])[-60:]
        self.vl = (self.vl + [self.v])[-60:]


class System:
    def __init__(self):
        self.r = Lcg(131)
        self.c, self.m, self.k, self.n = 18.0, 51.0, 6.0, 24.0
        self.cl, self.ml, self.kl, self.nl = [], [], [], []

    def step(self):
        r = self.r
        burst = r.rnd() * 30 if r.rnd() < 0.1 else 0
        self.c = cl(self.c + (r.rnd() - 0.5) * 12 + (20 - self.c) * 0.1 + burst, 1, 100)
        self.m = cl(self.m + (r.rnd() - 0.5) * 1.4 + (51 - self.m) * 0.05, 35, 90)
        self.k = cl(self.k + (r.rnd() - 0.5) * 8 + (8 - self.k) * 0.15 + burst * 0.5, 0, 100)
        self.n = cl(self.n + (r.rnd() - 0.5) * 12 + (24 - self.n) * 0.1 + burst * 0.6, 1, 100)
        self.cl = (self.cl + [self.c])[-60:]
        self.ml = (self.ml + [self.m])[-60:]
        self.kl = (self.kl + [self.k])[-60:]
        self.nl = (self.nl + [self.n])[-60:]


# ---------------------------------------------------------------------------
# path helpers
# ---------------------------------------------------------------------------
def points(data, w, h):
    n = len(data)
    return [(i * w / (n - 1), h - 1 - cl(v / 100, 0, 1) * (h - 2)) for i, v in enumerate(data)]


def f1(x):
    s = "%.1f" % x
    return s[:-2] if s.endswith(".0") else s


def line(pts):
    return " ".join(("L" if i else "M") + f1(x) + " " + f1(y) for i, (x, y) in enumerate(pts))


def dashed(pts, dash, gap):
    """Split a polyline into dash segments (Slint paths cannot dash)."""
    out = []
    pen = True
    left = dash
    cur = [pts[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        if seg == 0:
            continue
        pos = 0.0
        while pos < seg - 1e-9:
            take = min(left, seg - pos)
            t = (pos + take) / seg
            px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if pen:
                if len(cur) == 0:
                    sx = x0 + (x1 - x0) * pos / seg
                    sy = y0 + (y1 - y0) * pos / seg
                    cur = [(sx, sy)]
                cur.append((px, py))
            pos += take
            left -= take
            if left <= 1e-9:
                if pen and len(cur) > 1:
                    out.append(cur)
                cur = []
                pen = not pen
                left = dash if pen else gap
    if pen and len(cur) > 1:
        out.append(cur)
    return " ".join(line(c) for c in out)


def dotted(pts, gap):
    """Dots of zero length with round caps."""
    out = []
    pos_left = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        pos = pos_left
        while pos <= seg:
            t = pos / seg if seg else 0
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            out.append("M%s %s L%s %s" % (f1(x), f1(y), f1(x + 0.2), f1(y)))
            pos += gap
        pos_left = pos - seg
    return " ".join(out)


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


# ---------------------------------------------------------------------------
# collect frames
# ---------------------------------------------------------------------------
def run(model_cls, nframes):
    m = model_cls()
    for _ in range(WARMUP):
        m.step()
    frames = []
    for _ in range(nframes):
        frames.append(m)
        import copy
        m = copy.deepcopy(m)
        m.step()
    return frames


props = []  # (name, slint type, value text)


def add_strings(name, values):
    props.append((name, "[string]", "[" + ", ".join('"%s"' % esc(v) for v in values) + "]"))


def add_floats(name, values, fmt="%.1f"):
    props.append((name, "[float]", "[" + ", ".join((fmt % v).rstrip("0").rstrip(".") if "." in (fmt % v) else (fmt % v) for v in values) + "]"))


def add_strlist(name, values):
    add_strings(name, values)


cpu = run(Cpu, FRAMES)
mem = run(Memory, FRAMES)
dsk = run(Disk, FRAMES)
net = run(Network, FRAMES)
gpu = run(Gpu, FRAMES)
sysm = run(System, FRAMES)


def series(frames, attr, w, h, last=-1):
    return [points(getattr(m, attr), w, h) for m in frames]


# CPU
add_strings("cpu-l", [line(p) for p in series(cpu, "cpu", 304, 76)])
add_floats("cpu-l-y", [p[-1][1] for p in series(cpu, "cpu", 304, 76)])
add_strings("cpu-m", [line(p) for p in series(cpu, "cpu", 176, 90)])
add_floats("cpu-m-y", [p[-1][1] for p in series(cpu, "cpu", 176, 90)])
add_floats("cpu-val", [m.cpu[-1] for m in cpu])
props.append(("cpu-cores", "[[float]]", "[" + ", ".join("[" + ", ".join("%.0f" % m.core[i][-1] for i in range(16)) + "]" for m in cpu) + "]"))

# Memory
add_strings("mem-l", [line(p) for p in series(mem, "ram", 304, 56)])
add_floats("mem-l-y", [p[-1][1] for p in series(mem, "ram", 304, 56)])
add_strings("mem-swap-l", [dashed(p, 4, 3) for p in series(mem, "swap", 304, 56)])
add_floats("mem-val", [m.ram[-1] for m in mem])
add_floats("mem-swap-gb", [m.swap[-1] * 8 / 100 for m in mem], "%.2f")

# Disk
add_strings("disk-l", [line(p) for p in series(dsk, "rd", 304, 76)])
add_floats("disk-l-y", [p[-1][1] for p in series(dsk, "rd", 304, 76)])
add_strings("disk-w-l", [dashed(p, 4, 3) for p in series(dsk, "wr", 304, 76)])
add_strings("disk-m", [line(p) for p in series(dsk, "rd", 176, 90)])
add_floats("disk-m-y", [p[-1][1] for p in series(dsk, "rd", 176, 90)])
add_strings("disk-w-m", [dashed(p, 4, 3) for p in series(dsk, "wr", 176, 90)])
add_floats("disk-val", [m.act[-1] for m in dsk])
add_floats("disk-read", [m.rd[-1] for m in dsk])
add_floats("disk-write", [m.wr[-1] for m in dsk])

# Network
add_strings("net-l", [line(p) for p in series(net, "dl", 304, 76)])
add_floats("net-l-y", [p[-1][1] for p in series(net, "dl", 304, 76)])
add_strings("net-u-l", [dashed(p, 4, 3) for p in series(net, "ul", 304, 76)])
add_strings("net-m", [line(p) for p in series(net, "dl", 176, 90)])
add_floats("net-m-y", [p[-1][1] for p in series(net, "dl", 176, 90)])
add_strings("net-u-m", [dashed(p, 4, 3) for p in series(net, "ul", 176, 90)])
add_floats("net-down", [m.dl[-1] for m in net])
add_floats("net-up", [m.ul[-1] for m in net])

# GPU
add_strings("gpu-l", [line(p) for p in series(gpu, "gl", 304, 76)])
add_floats("gpu-l-y", [p[-1][1] for p in series(gpu, "gl", 304, 76)])
add_strings("gpu-v-l", [dashed(p, 4, 3) for p in series(gpu, "vl", 304, 76)])
add_strings("gpu-m", [line(p) for p in series(gpu, "gl", 176, 90)])
add_floats("gpu-m-y", [p[-1][1] for p in series(gpu, "gl", 176, 90)])
add_floats("gpu-val", [m.gl[-1] for m in gpu])
add_floats("gpu-vram", [m.vl[-1] for m in gpu])

# System widget: four tile sparklines (135 x 26) and one big chart (656 x 84)
for key, attr in (("cpu", "cl"), ("mem", "ml"), ("disk", "kl"), ("net", "nl")):
    add_strings("sys-%s-s" % key, [line(p) for p in series(sysm, attr, 135, 26)])
    add_floats("sys-%s-s-y" % key, [p[-1][1] for p in series(sysm, attr, 135, 26)])
add_strings("sys-cpu-b", [line(p) for p in series(sysm, "cl", 656, 84)])
add_floats("sys-cpu-b-y", [p[-1][1] for p in series(sysm, "cl", 656, 84)])
add_strings("sys-mem-b", [dashed(p, 6, 4) for p in series(sysm, "ml", 656, 84)])
add_strings("sys-net-b", [dotted(p, 5) for p in series(sysm, "nl", 656, 84)])
add_floats("sys-cpu", [m.cl[-1] for m in sysm])
add_floats("sys-mem", [m.ml[-1] for m in sysm])
add_floats("sys-disk", [m.kl[-1] for m in sysm])
add_floats("sys-net", [m.nl[-1] for m in sysm])

# Hot variants (frame 0 only): a graph that is already high, for warning and critical states.
def hot(frames, attr, w, h, lo, k):
    d = [lo + v * k for v in getattr(frames[0], attr)]
    return points(d, w, h)

for nm, fr, attr, lo_w, k_w, lo_c, k_c in (("cpu", cpu, "cpu", 76, 0.12, 91, 0.1), ("mem", mem, "ram", 77, 0.1, 91, 0.06),
                                             ("disk", dsk, "rd", 77, 0.1, 93, 0.05), ("net", net, "dl", 77, 0.1, 92, 0.06),
                                             ("gpu", gpu, "gl", 77, 0.1, 92, 0.06)):
    w_big, h_big = (304, 56) if nm == "mem" else (304, 76)
    add_strings("%s-warn" % nm, [line(hot(fr, attr, w_big, h_big, lo_w, k_w))])
    add_floats("%s-warn-y" % nm, [hot(fr, attr, w_big, h_big, lo_w, k_w)[-1][1]])
    add_strings("%s-crit" % nm, [line(hot(fr, attr, w_big, h_big, lo_c, k_c))])
    add_floats("%s-crit-y" % nm, [hot(fr, attr, w_big, h_big, lo_c, k_c)[-1][1]])

out = ["// GENERATED by tools/gen_mock.py. Do not edit by hand.",
       "// Sample data for the widgets: %d frames per live series. The app advances `Mock.tick` once a second." % FRAMES,
       "",
       "export global Mock {",
       "    in-out property <int> tick: 0;",
       "    out property <int> frames: %d;" % FRAMES]
for name, typ, val in props:
    out.append("    out property <%s> %s: %s;" % (typ, name, val))
out.append("}")
out.append("")
open(os.path.join(ROOT, "ui", "mock.slint"), "w").write("\n".join(out))
print("wrote ui/mock.slint, %d properties, %d bytes" % (len(props), len("\n".join(out))))
