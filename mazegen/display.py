"""
display.py  –  A-Maze-ing Cyber Edition  (v2.0 — enhanced)
===========================================================
All visual features work independently and compose cleanly:
  • 8 wall-character sets        (option  9)
  • PULSE WAVE FX                (option 10)
  • Animated BG wash  (5 modes)  (option 11)
  • 3-D shadow illusion          (option 12)
  • HUD sidebar panel            (option 13)
  • Twinkling star field         (option 14)
  • Neon-Cyberpunk mode          (option 15)
  • Animation speed              (option 16)
  • RAIN EFFECT                  (option 17)
  • PLASMA EFFECT                (option 18)
"""

import random
import time
import math
import sys
import select
import tty
from mazegen.config_parser import MazeConfig
import termios
import shutil
from typing import List, Optional, Set, Tuple, Dict
from mazegen.output_writer import write_output
from mazegen import MazeGenerator, NORTH, EAST, SOUTH, WEST

# ── ANSI helpers ──────────────────────────────────────────────
RESET = "\033[0m"
BOLD = "\033[1m"


def _fg(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


def _bg(r: int, g: int, b: int) -> str:
    return f"\033[48;2;{r};{g};{b}m"


def _clamp(v: int) -> int:
    return max(0, min(255, v))


def _term_size() -> Tuple[int, int]:
    size = shutil.get_terminal_size()
    return size.columns, size.lines


def _maze_dimensions(gen: MazeGenerator) -> Tuple[int, int]:
    CW = _cell_w()
    width = (2 * gen.width + 1) * CW
    height = (2 * gen.height + 1)
    return width, height


def _check_terminal(gen: MazeGenerator) -> bool:
    cols, rows = _term_size()
    maze_w, maze_h = _maze_dimensions(gen)
    w = sys.stdout.write
    HUD_VIS = 24
    GAP = 2
    MENU_W = 54

    rtxt = _fg(255, 0, 0)
    gtxt = _fg(0, 255, 0)
    num_color = _fg(255, 255, 0)

    ui_width = HUD_VIS + GAP + MENU_W
    required_w = max(maze_w, ui_width)
    required_h = maze_h + 5

    if cols < required_w or rows < required_h:
        lines = [
            f"{rtxt}{BOLD}=== Terminal too small! ==={RESET}",
            f"{gtxt}Need at least: {required_w}x{required_h}{RESET}",
            f"{rtxt}Current size: {num_color}{cols}x{rows}{RESET}",
            "Please resize terminal."
        ]

        w("\033[2J")

        start_row = (rows - len(lines)) // 2

        for i, line in enumerate(lines):
            line_len = len(_strip_ansi(line))
            start_col = (cols - line_len) // 2
            w(f"\033[{start_row + i + 1};{start_col + 1}H{line}")

        sys.stdout.flush()
        return False

    return True


def _strip_ansi(text: str) -> str:
    import re
    ansi_escape = re.compile(r"\033\[[^m]*m")
    return ansi_escape.sub('', text)


# ── Wall / floor character sets ───────────────────────────────
WALL_SETS: List[Tuple[str, str, str]] = [
    ("\u2593", " ", "\u2022"),
    ("\u2588", "\u2591", "\u00b7"),
    ("\u25a0", "\u00b7", "\u25cb"),
    ("\u25aa", " ", "\u25b8"),
    ("\u256c", " ", "\u2500"),
    ("\u25c6", "\u00b7", "\u25c7"),
    ("\u25b2", " ", "\u25ba"),
    ("#", ".", "*"),
]


PRESETS: List[Tuple[Tuple[int, int, int], ...]] = [
    # 0 STONE
    (
        (255, 255, 255), (220, 220, 220),
        (0, 255, 0), (0, 120, 255), (255, 50, 50), (255, 215, 0),
    ),
    # 1 OCEAN
    (
        (10, 30, 60), (200, 230, 255),
        (255, 140, 0), (0, 255, 255), (255, 0, 100), (255, 255, 0),
    ),
    # 2 VIOLET
    (
        (40, 0, 60), (230, 200, 255),
        (0, 255, 120), (255, 0, 255), (255, 80, 80), (255, 255, 0),
    ),
    # 3 FOREST
    (
        (0, 40, 0), (200, 255, 200),
        (0, 0, 255), (255, 0, 255), (255, 50, 50), (255, 215, 0),
    ),
    # 4 ABYSS
    (
        (0, 60, 80), (230, 250, 255),
        (255, 0, 255), (0, 120, 255), (255, 0, 0), (255, 200, 0),
    ),
    # 5 MONO
    (
        (0, 0, 0), (255, 255, 255),
        (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 215, 0),
    ),
    # 6 NEON CYBERPUNK
    (
        (15, 0, 35), (160, 0, 220),
        (0, 255, 200), (255, 0, 120), (0, 255, 255), (255, 40, 200),
    ),
]

# ── Global state ──────────────────────────────────────────────
WALL_SET_IDX: int = 0
CELL_W: int = 2
SHOW_42: bool = True
ANIMATE_42: bool = True
PATTERN_STYLE: int = 0
BG_ANIM: bool = False
BG_MODE: int = 0
ANIM_SPEED: float = 1.0
SHOW_STARS: bool = False
ILLUSION_3D: bool = False
SHOW_HUD: bool = False
NEON_CYBERPUNK: bool = False
PULSE_WAVE: bool = False
RAIN_EFFECT: bool = False
PLASMA: bool = False

# ── Rain state ────────────────────────────────────────────────
_rain_drops: List[Tuple[int, float, float]] = []
_rain_grid_w: int = 0


def _wall_set() -> Tuple[str, str, str]:
    return WALL_SETS[WALL_SET_IDX]


def _cell_w() -> int:
    return CELL_W


def _active_preset(user_preset: int) -> int:
    return 6 if NEON_CYBERPUNK else user_preset


# ── Pulse wave ────────────────────────────────────────────────
_PULSE_SPEED: float = 2.2
_PULSE_FREQ: float = 0.55


def _pulse_colour(
    base: Tuple[int, int, int],
    gx: int,
    gy: int,
    egx: int,
    egy: int,
    t: float,
) -> Tuple[int, int, int]:
    dist = math.sqrt((gx - egx) ** 2 + (gy - egy) ** 2)
    wave = (math.sin(dist * _PULSE_FREQ - t * _PULSE_SPEED) + 1.0) / 2.0
    scale = 0.40 + 0.70 * wave
    hshift = int(wave * 80)
    r = _clamp(int(base[0] * scale) + hshift)
    g = _clamp(int(base[1] * scale) + hshift // 3)
    b = _clamp(int(base[2] * scale))
    return r, g, b


# ── Star field ────────────────────────────────────────────────
_STAR_CHARS = ["\u00b7", ".", "+", "\u2726", "\u2727", "\u22c6"]
_star_pool: List[Tuple[int, int, float, str]] = []
_star_grid_size: Tuple[int, int] = (0, 0)


def _init_stars(DW: int, DH: int, n: int = 55) -> None:
    global _star_pool, _star_grid_size
    if (DW, DH) == _star_grid_size:
        return
    _star_grid_size = (DW, DH)
    _star_pool = [
        (
            random.randint(0, DH - 1),
            random.randint(0, DW - 1),
            random.uniform(0.0, 6.28),
            random.choice(_STAR_CHARS),
        )
        for _ in range(n)
    ]


def _build_star_set(t: float) -> Dict[Tuple[int, int],
                                      Tuple[int, int, int, str]]:
    result: Dict[Tuple[int, int], Tuple[int, int, int, str]] = {}
    for sr, sc, phase, ch in _star_pool:
        v = _clamp(int(70 + (math.sin(t * 1.6 + phase) + 1) * 90))
        result[(sr, sc)] = (v, v, _clamp(int(v * 0.5)), ch)
    return result


# ── Rain effect ───────────────────────────────────────────────

def _init_rain(DW: int) -> None:
    global _rain_drops, _rain_grid_w
    if DW == _rain_grid_w:
        return
    _rain_grid_w = DW
    _rain_drops = [
        (col, random.uniform(0.0, 30.0), random.uniform(0.4, 1.4))
        for col in range(DW)
        if random.random() < 0.40
    ]


def _update_rain(DH: int) -> None:
    global _rain_drops
    _rain_drops = [
        (col, (row + spd * 0.6) % (DH + 10), spd)
        for col, row, spd in _rain_drops
    ]


def _build_rain_set(DH: int) -> Dict[Tuple[int, int], float]:
    result: Dict[Tuple[int, int], float] = {}
    for col, row_pos, _ in _rain_drops:
        head = int(row_pos)
        tail_len = 7
        for i in range(tail_len):
            gy = head - i
            if 0 <= gy < DH:
                brightness = 1.0 - (i / tail_len) * 0.85
                if result.get((gy, col), 0.0) < brightness:
                    result[(gy, col)] = brightness
    return result


# ── Plasma effect ─────────────────────────────────────────────

def _plasma_colour(gx: int, gy: int, t: float) -> Tuple[int, int, int]:
    v = math.sin(gx * 0.30 + t * 1.1)
    v += math.sin(gy * 0.25 + t * 0.9)
    v += math.sin((gx + gy) * 0.20 + t * 1.3)
    v += math.sin(math.sqrt(gx * gx + gy * gy) * 0.18 - t * 1.0)
    hue = v / 8.0 + 0.5
    h6 = hue * 6.0
    seg = int(h6) % 6
    f = h6 - int(h6)
    q = 1.0 - f
    colour_map = [
        (1.0, f, 0.0),
        (q, 1.0, 0.0),
        (0.0, 1.0, f),
        (0.0, q, 1.0),
        (f, 0.0, 1.0),
        (1.0, 0.0, q),
    ]
    pr, pg, pb = colour_map[seg]
    bright = 200
    return (
        _clamp(int(pr * bright)),
        _clamp(int(pg * bright)),
        _clamp(int(pb * bright)),
    )


# ── Background wash ───────────────────────────────────────────
_BG_MODE_NAMES = ["Wave", "Pulse", "Gradient", "Scanline", "Aurora"]


def _row_bg(t: float, row_frac: float) -> Tuple[int, int, int]:
    if BG_MODE == 0:
        r = _clamp(int((math.sin(t * 0.5 + row_frac * 3) + 1) * 55))
        g = _clamp(int((math.sin(t * 0.4 + row_frac * 2 + 1) + 1) * 35))
        b = _clamp(int((math.sin(t * 0.6 + row_frac * 4 + 2) + 1) * 80))
    elif BG_MODE == 1:
        v = (math.sin(t * 1.5) + 1) / 2
        r = _clamp(int(v * 80))
        g = _clamp(int(v * 40))
        b = _clamp(int(v * 120))
    elif BG_MODE == 2:
        r = _clamp(int(row_frac * 100))
        g = _clamp(int(20 + math.sin(t * 0.4) * 20))
        b = _clamp(int((1 - row_frac) * 120 + math.sin(t * 0.6) * 30))
    elif BG_MODE == 3:
        scan = (t * 0.6) % 1.0
        dist = abs(row_frac - scan)
        v = _clamp(int(max(0, 1 - dist * 8) * 160))
        r, g, b = v // 4, v // 4, v
    else:
        r = _clamp(int((math.sin(t * 0.5 + row_frac * 6) + 1) * 50))
        g = _clamp(int((math.sin(t * 0.4 + row_frac * 5 + 1) + 1) * 90))
        b = _clamp(int((math.sin(t * 0.6 + row_frac * 7 + 2) + 1) * 70))
    return r, g, b


# ── 3-D shadow ────────────────────────────────────────────────
def _shadow_fg(rgb: Tuple[int, int, int]) -> str:
    r, g, b = rgb
    return _fg(_clamp(r // 4), _clamp(g // 4), _clamp(b // 4))


# ── 42 colour animation ───────────────────────────────────────
def _c42(base: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    r, g, b = base
    if not ANIMATE_42:
        return r, g, b
    if PATTERN_STYLE == 1:
        m = 0.5 + 0.5 * (math.sin(t * 4) + 1) / 2
        return _clamp(int(r * m)), _clamp(int(g * m)), _clamp(int(b * m))
    if PATTERN_STYLE == 2:
        glow = int((math.sin(t * 6) + 1) * 100)
        return _clamp(r + glow), _clamp(g + glow // 2), b
    if PATTERN_STYLE == 3:
        return (
            _clamp(int((math.sin(t * 2.0) + 1) * 127)),
            _clamp(int((math.sin(t * 2.0 + 2.1) + 1) * 127)),
            _clamp(int((math.sin(t * 2.0 + 4.2) + 1) * 127)),
        )
    return r, g, b


# ── HUD sidebar ───────────────────────────────────────────────
_THEME_NAMES = ["STONE", "OCEAN", "VIOLET", "FOREST", "ABYSS", "MONO"]


def _build_hud(
    gen: MazeGenerator, t: float, user_preset: int
) -> List[str]:
    HW = 20
    p = _clamp(int((math.sin(t * 3) + 1) * 127))
    wch, _, _ = _wall_set()
    cw = _cell_w()
    pname = "NEON" if NEON_CYBERPUNK else _THEME_NAMES[user_preset % 6]
    fx_on = []
    if BG_ANIM:
        fx_on.append("BG")
    if ILLUSION_3D:
        fx_on.append("3D")
    if SHOW_STARS:
        fx_on.append("\u2605")
    if NEON_CYBERPUNK:
        fx_on.append("NEON")
    if PULSE_WAVE:
        fx_on.append("~W")
    if RAIN_EFFECT:
        fx_on.append("RN")
    if PLASMA:
        fx_on.append("PL")
    fx = " ".join(fx_on) or "none"

    BC = _fg(0, 255, 200) if NEON_CYBERPUNK else _fg(80, 180, 255)
    VC = _fg(220, 220, 255)
    KC = _fg(120, 120, 200)
    HC = _fg(p, 255, _clamp(255 - p))

    TOP = BC + "\u2554" + "\u2550" * (HW + 2) + "\u2557" + RESET
    MID = BC + "\u2560" + "\u2550" * (HW + 2) + "\u2563" + RESET
    BOT = BC + "\u255a" + "\u2550" * (HW + 2) + "\u255d" + RESET

    def hdr(text: str) -> str:
        t2 = text[:HW]
        pad = HW - len(t2)
        lp = pad // 2
        rp = pad - lp
        return (
            BC + "\u2551 " + _fg(0, 255, 180) + BOLD
            + " " * lp + t2 + " " * rp
            + RESET + BC + " \u2551" + RESET
        )

    def row(key: str, val: str) -> str:
        vw = HW - 7
        val = str(val)[:vw]
        return (
            BC + "\u2551 " + KC + f"{key:<6}" + RESET + "="
            + VC + f"{val:<{vw}}" + BC + " \u2551" + RESET
        )

    def fxrow(text: str) -> str:
        text = text[:HW]
        return BC + "\u2551 " + HC + f"{text:<{HW}}" + BC + " \u2551" + RESET

    plen = len(gen.solution_path) if gen.solution_path else 0

    return [
        TOP,
        hdr("A-MAZE-ING HUD"),
        MID,
        row("size", f"{gen.width}x{gen.height}"),
        row("seed", str(gen.seed or 0)),
        row("path", str(plen)),
        MID,
        row("wall", f"[{wch}] cw={cw}"),
        row("theme", pname),
        row("42-fx", ["solid", "pulse", "glow", "rainbow"][PATTERN_STYLE]),
        MID,
        fxrow(fx),
        BOT,
    ]


# ── Cell type constants ───────────────────────────────────────
T_WALL, T_FLOOR, T_PATH, T_ENTRY, T_EXIT, T_42, T_CUR = range(7)


# ── Core render ───────────────────────────────────────────────
def _render(
    gen: MazeGenerator,
    show_path: bool,
    user_preset: int,
    t: float = 0.0,
    highlight: Optional[Tuple[int, int]] = None,
    visible_42: Optional[Set[Tuple[int, int]]] = None,
) -> List[str]:
    t = t * ANIM_SPEED
    W, H = gen.width, gen.height
    DW, DH = 2 * W + 1, 2 * H + 1
    CW = _cell_w()
    WALL_CH, FLOOR_CH, PATH_CH = _wall_set()
    pi = _active_preset(user_preset)
    c_wall, c_floor, c_path, c_entry, c_exit, c_42 = PRESETS[pi]

    tgrid: List[List[int]] = [[T_WALL] * DW for _ in range(DH)]
    cells42 = visible_42 if visible_42 is not None else gen.cells_42

    for cy in range(H):
        for cx in range(W):
            cell = gen.grid[cy][cx]
            gx, gy = 2 * cx + 1, 2 * cy + 1
            if SHOW_42 and (cx, cy) in cells42:
                tgrid[gy][gx] = T_42
                continue
            tgrid[gy][gx] = T_FLOOR
            if not (cell & NORTH):
                tgrid[gy - 1][gx] = T_FLOOR
            if not (cell & SOUTH):
                tgrid[gy + 1][gx] = T_FLOOR
            if not (cell & WEST):
                tgrid[gy][gx - 1] = T_FLOOR
            if not (cell & EAST):
                tgrid[gy][gx + 1] = T_FLOOR

    if show_path and gen.solution_path:
        for cx, cy in gen.solution_path:
            tgrid[2 * cy + 1][2 * cx + 1] = T_PATH

    ex, ey = gen.entry
    xx, xy = gen.exit
    tgrid[2 * ey + 1][2 * ex + 1] = T_ENTRY
    tgrid[2 * xy + 1][2 * xx + 1] = T_EXIT

    if highlight is not None:
        hx, hy = highlight
        tgrid[2 * hy + 1][2 * hx + 1] = T_CUR

    r42, g42, b42 = _c42(c_42, t)
    egx, egy = 2 * ex + 1, 2 * ey + 1

    star_set: Dict[Tuple[int, int], Tuple[int, int, int, str]] = {}
    if SHOW_STARS:
        _init_stars(DW, DH, n=55)
        star_set = _build_star_set(t)

    rain_set: Dict[Tuple[int, int], float] = {}
    if RAIN_EFFECT:
        _init_rain(DW)
        _update_rain(DH)
        rain_set = _build_rain_set(DH)

    output: List[str] = []

    for gy in range(DH):
        parts: List[str] = []

        bg_r, bg_g, bg_b = 0, 0, 0
        if BG_ANIM:
            bg_r, bg_g, bg_b = _row_bg(t, gy / max(1, DH - 1))

        def _blend(r: int, g: int, b: int) -> Tuple[int, int, int]:
            if not BG_ANIM:
                return r, g, b
            return (
                _clamp(r + bg_r // 2),
                _clamp(g + bg_g // 2),
                _clamp(b + bg_b // 2),
            )

        for gx in range(DW):
            cell_t = tgrid[gy][gx]

            if cell_t == T_WALL:
                wr, wg, wb = c_wall
                if PLASMA:
                    wr, wg, wb = _plasma_colour(gx, gy, t)
                elif PULSE_WAVE:
                    wr, wg, wb = _pulse_colour(
                        (wr, wg, wb), gx, gy, egx, egy, t
                    )
                elif NEON_CYBERPUNK:
                    flk = (
                        0.78
                        + 0.22 * math.sin(t * 8 + gy * 0.4 + gx * 0.35)
                    )
                    wr = _clamp(int(wr * flk))
                    wg = _clamp(int(wg * flk))
                    wb = _clamp(int(wb * flk))
                wr, wg, wb = _blend(wr, wg, wb)
                if RAIN_EFFECT:
                    bright = rain_set.get((gy, gx), 0.0)
                    if bright > 0.0:
                        if bright > 0.85:
                            wr = _clamp(
                                int(wr * (1 - bright) + 200 * bright)
                            )
                            wg = _clamp(
                                int(wg * (1 - bright) + 255 * bright)
                            )
                            wb = _clamp(
                                int(wb * (1 - bright) + 200 * bright)
                            )
                        else:
                            wr = _clamp(
                                int(wr * (1 - bright) + 0 * bright)
                            )
                            wg = _clamp(
                                int(wg * (1 - bright) + 255 * bright)
                            )
                            wb = _clamp(
                                int(wb * (1 - bright) + 70 * bright)
                            )
                if ILLUSION_3D and CW >= 2:
                    parts.append(
                        _fg(wr, wg, wb) + WALL_CH * (CW - 1)
                        + _shadow_fg((wr, wg, wb)) + WALL_CH + RESET
                    )
                else:
                    parts.append(_fg(wr, wg, wb) + WALL_CH * CW + RESET)

            elif cell_t == T_FLOOR:
                star_data = star_set.get((gy, gx)) if SHOW_STARS else None
                if star_data:
                    sr, sg, sb, sch = star_data
                    parts.append(
                        _fg(sr, sg, sb) + sch
                        + FLOOR_CH * (CW - 1) + RESET
                    )
                else:
                    parts.append(FLOOR_CH * CW)

            elif cell_t == T_PATH:
                pr, pg, pb = _blend(*c_path)
                parts.append(_fg(pr, pg, pb) + PATH_CH * CW + RESET)

            elif cell_t == T_ENTRY:
                pulse = _clamp(int((math.sin(t * 4) + 1) * 100))
                er, eg, eb = c_entry
                er2, eg2, eb2 = _blend(_clamp(er + pulse), eg, eb)
                parts.append(
                    _fg(er2, eg2, eb2) + BOLD + "E" * CW + RESET
                )

            elif cell_t == T_EXIT:
                pulse = _clamp(int((math.sin(t * 4 + 1.5) + 1) * 100))
                xr, xg, xb = c_exit
                xr2, xg2, xb2 = _blend(xr, xg, _clamp(xb + pulse))
                parts.append(
                    _fg(xr2, xg2, xb2) + BOLD + "X" * CW + RESET
                )

            elif cell_t == T_42:
                cr42, cg42, cb42 = _blend(r42, g42, b42)
                if NEON_CYBERPUNK:
                    parts.append(
                        _bg(18, 0, 45) + _fg(cr42, cg42, cb42)
                        + WALL_CH * CW + RESET
                    )
                else:
                    parts.append(
                        _fg(cr42, cg42, cb42) + WALL_CH * CW + RESET
                    )

            elif cell_t == T_CUR:
                pulse = _clamp(int((math.sin(t * 8) + 1) * 127))
                parts.append(
                    _fg(255, pulse, 255) + "\u258c" * CW + RESET
                )

        parts.append(RESET)
        output.append("".join(parts))

    return output


# ── Interactive mode ──────────────────────────────────────────

def run_interactive(
    gen: MazeGenerator,
    config: MazeConfig
) -> None:
    global SHOW_42, PATTERN_STYLE
    global BG_ANIM, BG_MODE, ANIM_SPEED
    global SHOW_STARS, ILLUSION_3D, SHOW_HUD
    global NEON_CYBERPUNK, WALL_SET_IDX
    global PULSE_WAVE, RAIN_EFFECT, _rain_grid_w
    global PLASMA

    show_path = False
    user_preset = 0

    STYLE_NAMES = ["solid", "pulse", "glow", "rainbow"]
    _SPEEDS = [0.25, 0.5, 1.0, 2.0, 4.0]
    _LABELS = [
        "\u00bc\u00d7  Slow-mo",
        "\u00bd\u00d7  Slow",
        "1\u00d7  Normal",
        "2\u00d7  Fast",
        "4\u00d7  Turbo",
    ]

    HUD_VIS = 24
    GAP = 2

    # ── Footer: HUD (if on) + menu ────────────────────────────
    def _draw_footer(menu_rows_: List[str], buf_: str = "") -> None:
        w = sys.stdout.write
        hud_rows = (
            _build_hud(gen, time.time(), user_preset) if SHOW_HUD else []
        )
        n_menu = len(menu_rows_)
        n_hud = len(hud_rows)
        hud_offset = max(0, (n_menu - n_hud) // 2)

        for i in range(n_menu):
            mrow = menu_rows_[i]
            hi = i - hud_offset
            if SHOW_HUD:
                if 0 <= hi < n_hud:
                    hrow = hud_rows[hi]
                    hplain = _strip_ansi(hrow)
                    hpad = " " * max(0, HUD_VIS - len(hplain))
                    w(hrow + hpad + " " * GAP + mrow + "\r\n")
                else:
                    w(" " * HUD_VIS + " " * GAP + mrow + "\r\n")
            else:
                w(mrow + "\r\n")

        prompt_prefix = (" " * HUD_VIS + " " * GAP) if SHOW_HUD else ""
        w(prompt_prefix + "  Choice \u203a " + buf_)
        sys.stdout.flush()

    # ── Full clear + redraw ───────────────────────────────────
    def _full_draw(menu_rows_: List[str], buf_: str = "") -> None:
        w = sys.stdout.write
        w("\033[?25l\033[2J\033[H")
        if not gen.pattern_fits:
            w(
                _fg(255, 80, 80)
                + "\u26a0  Maze too small for '42' pattern."
                + RESET + "\r\n"
            )
        maze_lines = _render(gen, show_path, user_preset, t=time.time())
        for line in maze_lines:
            w(line + "\r\n")
        _draw_footer(menu_rows_, buf_)
        w("\033[?25h")
        sys.stdout.flush()

    # ── Repaint maze rows in-place (cursor jump, NO screen erase) ────
    def _redraw_maze_inplace(maze_lines: List[str]) -> None:
        w = sys.stdout.write
        w("\033[H")
        if not gen.pattern_fits:
            w(
                _fg(255, 80, 80)
                + "\u26a0  Maze too small for '42' pattern."
                + RESET + "\r\n"
            )
        for line in maze_lines:
            w(line + "\r\n")
        sys.stdout.flush()

    def _prepare_anim(menu_rows_: List[str]) -> int:
        maze_h = 2 * gen.height + 1
        footer_row = maze_h + 1
        sys.stdout.write("\033[?25l\033[2J\033[H")
        if not gen.pattern_fits:
            sys.stdout.write(
                _fg(255, 80, 80)
                + "\u26a0  Maze too small for '42' pattern."
                + RESET + "\r\n"
            )
        sys.stdout.write(f"\033[{footer_row}H\r\n")
        _draw_footer(menu_rows_, "")
        sys.stdout.flush()
        return footer_row

    # ── Redraw footer in-place without touching the maze ─────────
    def _redraw_footer_inplace(menu_rows_: List[str], footer_row: int) -> None:
        # Jump to footer row, erase everything below, then redraw clean
        sys.stdout.write(f"\033[{footer_row}H\033[J")
        _draw_footer(menu_rows_, "")
        sys.stdout.flush()

    # ── Main loop ─────────────────────────────────────────────
    while True:
        wch, _, _ = _wall_set()
        pname = "NEON" if NEON_CYBERPUNK else _THEME_NAMES[user_preset % 6]

        if NEON_CYBERPUNK:
            CB = _fg(0, 220, 255)
            CT = _fg(255, 40, 200)
            CS = _fg(180, 0, 255)
            CN = _fg(255, 50, 200)
            CL = _fg(0, 255, 200)
            CK = _fg(160, 80, 255)
            CV = _fg(255, 230, 80)
            CO = _fg(0, 255, 160)
            CF = _fg(255, 30, 80)
            CD = _fg(60, 0, 120)
            CA = _fg(255, 120, 0)
        else:
            CB = _fg(55, 155, 255)
            CT = _fg(255, 215, 0)
            CS = _fg(90, 130, 220)
            CN = _fg(255, 185, 0)
            CL = _fg(155, 255, 175)
            CK = _fg(115, 170, 255)
            CV = _fg(255, 225, 120)
            CO = _fg(50, 255, 130)
            CF = _fg(255, 65, 65)
            CD = _fg(55, 70, 115)
            CA = _fg(255, 150, 50)

        IW = 50
        LW = 16

        def _R(c: str, v: int) -> str:
            return (
                f"{CB}\u2551{RESET} {c}"
                f"{' ' * max(0, IW - v)} {CB}\u2551{RESET}"
            )

        TOP = f"{CB}\u2554{'\u2550' * (IW + 2)}\u2557{RESET}"
        BOT = f"{CB}\u255a{'\u2550' * (IW + 2)}\u255d{RESET}"
        SEP = f"{CB}\u2560{'\u2550' * (IW + 2)}\u2563{RESET}"

        def _SEC(label: str) -> Tuple[str, int]:
            inner = f" \u25c6 {label} \u25c6 "
            total = IW - len(inner)
            ld = total // 2
            rd = total - ld
            return (
                CD + "\u2500" * ld + CS + BOLD + inner + RESET
                + CD + "\u2500" * rd + RESET,
                IW
            )

        def _pill(flag: bool) -> Tuple[str, int]:
            if flag:
                return CO + "\u25b6ON" + RESET, 3
            return CF + "OFF" + RESET, 3

        def _tog(label: str, val: bool) -> Tuple[str, int]:
            p, pl = _pill(val)
            return f"{CK}{label}{RESET}:{p}", len(label) + 1 + pl

        def _kv(k: str, v: str, vlen: int) -> Tuple[str, int]:
            return (
                f"{CK}{k}{RESET}{CD}={RESET}{CV}{v}{RESET}",
                len(k) + 1 + vlen,
            )

        ttxt = "\u2726  A\u00b7MAZE\u00b7ING  CYBER  \u2726"
        tvis = len(ttxt)
        tpad = (IW - tvis) // 2
        tansi = (
            " " * tpad + BOLD + CT + ttxt + RESET
            + " " * (IW - tvis - tpad)
        )

        kv_theme, l_th = _kv("Theme", f"{pname:<6}", 6)
        kv_wall, l_wa = _kv("Wall", f"[{wch}]", 3)
        kv_fx, l_fx = _kv(
            "FX", f"{STYLE_NAMES[PATTERN_STYLE]:<7}", 7
        )
        kv_sp, l_sp = _kv(
            "Spd", f"{ANIM_SPEED}x", len(f"{ANIM_SPEED}x")
        )
        st1 = f"{kv_theme}  {kv_wall}  {kv_fx}  {kv_sp}"
        st1v = l_th + 2 + l_wa + 2 + l_fx + 2 + l_sp

        tg_ne, tl_ne = _tog("Neon", NEON_CYBERPUNK)
        tg_bg, tl_bg = _tog("BG", BG_ANIM)
        tg_3d, tl_3d = _tog("3D", ILLUSION_3D)
        tg_st, tl_st = _tog("\u2605", SHOW_STARS)
        tg_hd, tl_hd = _tog("HUD", SHOW_HUD)
        tg_pw, tl_pw = _tog("~W", PULSE_WAVE)
        tg_rn, tl_rn = _tog("RN", RAIN_EFFECT)
        tg_pl, tl_pl = _tog("PL", PLASMA)
        # Row 2a: six toggles (fits IW=50)
        st2 = f"{tg_ne}  {tg_bg}  {tg_3d}  {tg_st}  {tg_hd}  {tg_pw}"
        st2v = (
            tl_ne + 2 + tl_bg + 2 + tl_3d
            + 2 + tl_st + 2 + tl_hd + 2 + tl_pw
        )
        # Row 2b: Rain + Plasma on their own line
        st3 = f"{tg_rn}  {tg_pl}"
        st3v = tl_rn + 2 + tl_pl

        _si = _SPEEDS.index(ANIM_SPEED) if ANIM_SPEED in _SPEEDS else 2
        _bar = (
            CO + "\u2588" * (_si + 1) + RESET
            + CD + "\u2591" * (4 - _si) + RESET
        )
        _barlbl = CA + _LABELS[_si].split()[0] + RESET
        _bg_nm = _BG_MODE_NAMES[BG_MODE] if BG_ANIM else "\u2500" * 5
        sprow = (
            f"{CK}Spd{RESET} {_bar} {_barlbl}  "
            f"{CK}BG:{RESET}{CV}{_bg_nm:<9}{RESET}  "
            f"{CK}W:{RESET}{CV}{wch}{RESET}"
        )
        spvis = 3 + 1 + 5 + 1 + 2 + 2 + 3 + 9 + 2 + 2 + 1

        def _P(
            i1: str, n1: str, l1: str,
            i2: str = "", n2: str = "", l2: str = "",
        ) -> Tuple[str, int]:
            left = (
                f"{CD}{i1}{RESET} {CN}{n1:>2}.{RESET}"
                f"{CL}{l1:<{LW}}{RESET}"
            )
            vis = 2 + 3 + LW
            if n2.strip():
                right = (
                    f"{CD}{i2}{RESET} {CN}{n2:>2}.{RESET}"
                    f"{CL}{l2:<{LW}}{RESET}"
                )
                vis += 1 + 2 + 3 + LW
                return left + " " + right, vis
            return left, vis

        _bg_lbl = (
            f"BG:{_BG_MODE_NAMES[BG_MODE]}" if BG_ANIM else "BG anim"
        )
        _sp_lbl = _LABELS[_si][:LW]
        _pw_lbl = "Pulse:ON " if PULSE_WAVE else "Pulse:OFF"
        _rn_lbl = "Rain: ON " if RAIN_EFFECT else "Rain: OFF"
        _pl_lbl = "Plasma:ON" if PLASMA else "PlasmaOFF"

        p1, v1 = _P(
            "\u27f3", " 1", "Re-generate", "\u21cc", " 2", "Path on/off"
        )
        p2, v2 = _P(
            "\u25b7", " 3", "Anim path", "\u25c8", " 4", "Next theme"
        )
        p3, v3 = _P(
            "\u2715", " 5", "Quit", "\u2b21", " 6", "Toggle 42"
        )
        p4, v4 = _P(
            "\u2726", " 7", "42 FX style", "\u25b8", " 8", "Animate 42"
        )
        p5, v5 = _P(
            "\u25a3", " 9", "Wall chars", "~", "10", _pw_lbl
        )
        p6, v6 = _P(
            "\u224b", "11", _bg_lbl[:LW], "\u25a7", "12", "3-D shadow"
        )
        p7, v7 = _P(
            "\u229f", "13", "HUD panel", "\u2605", "14", "Star field"
        )
        p8, v8 = _P("!", "15", "Neon mode", ">", "16", _sp_lbl)
        p9, v9 = _P("~", "17", _rn_lbl, "\u25c9", "18", _pl_lbl)

        menu_rows = [
            "",
            TOP,
            _R(tansi, IW),
            SEP,
            _R(st1, st1v),
            _R(st2, st2v),
            _R(st3, st3v),
            SEP,
            _R(sprow, spvis),
            SEP,
            _R(*_SEC("MAZE CONTROLS")),
            _R(p1, v1), _R(p2, v2), _R(p3, v3), _R(p4, v4),
            _R(*_SEC("VISUAL FX")),
            _R(p5, v5), _R(p6, v6), _R(p7, v7), _R(p8, v8),
            _R(*_SEC("DISPLAY")),
            _R(p9, v9),
            BOT,
            "",
        ]

        # ── Draw everything ───────────────────────────────────
        _full_draw(menu_rows)

        # ── Input: live loop when animated effects are on ─────
        choice = ""

        if True:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                buf = ""
                while True:
                    while not _check_terminal(gen):
                        time.sleep(0.2)
                    rdy, _, _ = select.select([sys.stdin], [], [], 0.05)
                    if rdy:
                        ch = sys.stdin.read(1)
                        if ch in ("\r", "\n"):
                            choice = buf.strip()
                            break
                        elif ch in ("\x7f", "\x08"):
                            buf = buf[:-1]
                        elif ch in ("\x03", "\x04"):
                            choice = "5"
                            break
                        elif ch.isdigit():
                            buf += ch
                            if buf[0] != "1":
                                choice = buf.strip()
                                break
                            elif len(buf) >= 2:
                                choice = buf.strip()
                                break
                        elif ch.isprintable():
                            buf += ch
                    else:
                        _full_draw(menu_rows, buf)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        # ── Choice handlers ───────────────────────────────────

        if choice == "1":
            _prepare_anim(menu_rows)
            for step in gen.generate_stepwise():
                lines = _render(
                    gen, False, user_preset,
                    t=time.time(), highlight=step,
                )
                _redraw_maze_inplace(lines)
                time.sleep(0.01)
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()
            try:
                write_output(
                    gen, config.output_file
                )
            except Exception:
                pass

        elif choice == "2":
            show_path = not show_path

        elif choice == "3":
            if gen.solution_path:
                saved = gen.solution_path[:]
                footer_row = _prepare_anim(menu_rows)
                for i in range(1, len(saved) + 1):
                    gen.solution_path = saved[:i]
                    frame = _render(
                        gen, True, user_preset,
                        t=time.time(), highlight=saved[i - 1],
                    )
                    _redraw_maze_inplace(frame)
                    # Redraw footer so HUD path counter increments live
                    _redraw_footer_inplace(menu_rows, footer_row)
                    time.sleep(0.06)
                gen.solution_path = saved
                sys.stdout.write("\033[?25h")
                sys.stdout.flush()

        elif choice == "4":
            user_preset = (user_preset + 1) % 6

        elif choice == "5":
            break

        elif choice == "6":
            SHOW_42 = not SHOW_42

        elif choice == "7":
            PATTERN_STYLE = (PATTERN_STYLE + 1) % 4

        elif choice == "8":
            if gen.cells_42:
                W2, H2 = gen.width, gen.height
                _prepare_anim(menu_rows)
                revealed: Set[Tuple[int, int]] = set()
                for sweep_y in range(H2 + 2):
                    for cx, cy in gen.cells_42:
                        if cy <= sweep_y:
                            revealed.add((cx, cy))
                    hl = (W2 // 2, sweep_y) if sweep_y < H2 else None
                    frame = _render(
                        gen, False, user_preset,
                        t=time.time(), visible_42=revealed, highlight=hl,
                    )
                    _redraw_maze_inplace(frame)
                    time.sleep(0.10)
                sys.stdout.write("\033[?25h")
                sys.stdout.flush()

        elif choice == "9":
            WALL_SET_IDX = (WALL_SET_IDX + 1) % len(WALL_SETS)

        elif choice == "10":
            PULSE_WAVE = not PULSE_WAVE

        elif choice == "11":
            if not BG_ANIM:
                BG_ANIM = True
            else:
                next_mode = (BG_MODE + 1) % len(_BG_MODE_NAMES)
                if next_mode == 0:
                    BG_ANIM = False
                    BG_MODE = 0
                else:
                    BG_MODE = next_mode

        elif choice == "12":
            ILLUSION_3D = not ILLUSION_3D

        elif choice == "13":
            SHOW_HUD = not SHOW_HUD

        elif choice == "14":
            SHOW_STARS = not SHOW_STARS

        elif choice == "15":
            NEON_CYBERPUNK = not NEON_CYBERPUNK

        elif choice == "16":
            cur_i = (
                _SPEEDS.index(ANIM_SPEED) if ANIM_SPEED in _SPEEDS else 2
            )
            cur_i = (cur_i + 1) % len(_SPEEDS)
            ANIM_SPEED = _SPEEDS[cur_i]

        elif choice == "17":
            RAIN_EFFECT = not RAIN_EFFECT
            if RAIN_EFFECT:
                _rain_grid_w = 0

        elif choice == "18":
            PLASMA = not PLASMA
