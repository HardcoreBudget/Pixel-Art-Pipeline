"""The battle UI kit, drawn pixel by pixel in the scene palette: framed panels, HP/MP bars (with the lost-HP
'ghost' that drains after a hit), 9x9 icons (menu verbs and lock types), the menu cursor, lock plates, name plates."""
import numpy as np

from px import C, canvas, blit, rect, put, art
from font import text, SMALL, BIG


def panel(w, h, trim="gold2", fill="night1", top="night2"):
    """A framed panel: ink border with cut corners, a 1-px trim, a lighter top inner row."""
    img = canvas(w, h)
    rect(img, 1, 0, w - 2, h, "ink"); rect(img, 0, 1, w, h - 2, "ink")
    rect(img, 2, 1, w - 4, h - 2, trim); rect(img, 1, 2, w - 2, h - 4, trim)
    rect(img, 2, 2, w - 4, h - 4, fill)
    rect(img, 2, 2, w - 4, 1, top)
    # a darker trim pixel at each inner corner reads as a rivet
    for x, y in ((2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)):
        put(img, x, y, "gold3" if trim == "gold2" else trim)
    return img


def bar(w, frac, ghost=None, kind="hp"):
    """A 5-px-high bar: ink frame, dark trough, fill in two tones; ghost (>= frac) shows lost HP in pale fire."""
    ramps = {"hp": ("moss3", "moss5", "moss2"), "mp": ("water4", "glow1", "water3"),
             "boss": ("crimson2", "crimson4", "crimson1"), "low": ("fire3", "fire5", "fire2")}
    body, hi, lo = ramps[kind]
    img = canvas(w, 5)
    rect(img, 1, 0, w - 2, 5, "ink"); rect(img, 0, 1, w, 3, "ink")
    rect(img, 1, 1, w - 2, 3, "night0")
    inner = w - 2
    n = int(round(inner * max(0.0, min(1.0, frac))))
    if ghost is not None and ghost > frac:
        g = int(round(inner * min(1.0, ghost)))
        rect(img, 1 + n, 1, g - n, 3, "fire4")
        rect(img, 1 + n, 3, g - n, 1, "fire3")
    if n:
        rect(img, 1, 1, n, 3, body)
        rect(img, 1, 1, n, 1, hi)
        rect(img, 1, 3, n, 1, lo)
    return img


K = {"o": "ink", "s": "silver1", "S": "silver2", "W": "silver3", "g": "gold1", "G": "gold2", "Y": "gold3",
     "w": "wood2", "d": "wood1", "b": "wood3", "f": "fire4", "F": "fire5", "h": "fire6", "c": "crimson2",
     "C": "crimson3", "t": "water3", "T": "water5", "l": "glow1", "L": "glow2", "v": "violet3", "V": "violet4",
     "m": "stone3", "M": "stone4"}

ICONS = {
    "sword": ["......ooo",
              ".....oWSo",
              "....oWSso",
              "...oWSso.",
              "o.oWSso..",
              "oGoSso...",
              ".oGoo....",
              "oGoGo....",
              "oo..o...."],
    "star":  ["....o....",
              "...oYo...",
              "...oYo...",
              "ooooGoooo",
              "oYYGGGYYo",
              ".oGGGGGo.",
              "..oGGGo..",
              ".oGGoGGo.",
              ".ooo.ooo."],
    "bag":   ["...ooo...",
              "..obdbo..",
              "...odo...",
              "..obbbo..",
              ".obbbbbo.",
              "obbwCwbbo",
              "obwwwwwbo",
              "obwwwwwdo",
              ".ooooooo."],
    "shield": ["ooooooooo",
               "oWSSoSSso",
               "oSSSoSSso",
               "ooooooooo",
               "oSSSoSSso",
               "oSSSoSsso",
               ".oSSoSso.",
               "..oSoso..",
               "...ooo..."],
    "sun":   ["....f....",
              ".f..F..f.",
              "...ooo...",
              "..oFhFo..",
              "fFohhhoFf",
              "..oFhFo..",
              "...ooo...",
              ".f..F..f.",
              "....f...."],
    "moon":  ["...ooo...",
              "..oTTo...",
              ".oTTo....",
              "oTTo.....",
              "oTTo.....",
              "oTTo.....",
              ".oTTo...o",
              "..oTTooTo",
              "...ooooo."],
}


def icon(name):
    return art(ICONS[name], K)


def cursor(frame=0):
    """A pointing gem cursor; bobs 1 px on odd frames."""
    rows = ["oo....",
            "oYoo..",
            "oYYGoo",
            "oYGGGo",
            "oGGgoo",
            "oggoo.",
            "oo...."]
    img = canvas(6, 8)
    return art(rows, K, 0, 1 if frame % 2 else 0, img)


def lock_plate(kind, state="whole", t=0):
    """A lock: a 13x13 plate around an icon. state: 'whole', 'crack' (flashes), 'gone' (shards, t = 0..3)."""
    img = canvas(13, 13)
    if state == "gone":
        # four shards flying outward from the plate's corners, fading by t
        for (sx, sy, dx, dy) in ((2, 2, -1, -1), (9, 2, 1, -1), (2, 9, -1, 1), (9, 9, 1, 1)):
            x, y = sx + dx * t, sy + dy * t
            col = "gold3" if t < 2 else "gold1"
            for (a, b) in ((0, 0), (1, 0), (0, 1)):
                if 0 <= x + a < 13 and 0 <= y + b < 13 and t < 4:
                    put(img, x + a, y + b, col)
        return img
    trim = "silver3" if state == "crack" else "silver1"
    rect(img, 1, 0, 11, 13, "ink"); rect(img, 0, 1, 13, 11, "ink")
    rect(img, 1, 1, 11, 11, trim)
    rect(img, 2, 2, 9, 9, "night0" if state == "whole" else "night3")
    blit(img, icon(kind), 2, 2)
    if state == "crack":
        for (x, y) in ((3, 1), (4, 2), (4, 3), (5, 4), (8, 8), (9, 9), (9, 10)):
            put(img, x, y, "silver3")
    return img


def name_plate(name, frac, ghost=None, w=86, kind="boss"):
    img = canvas(w, 16)
    blit(img, panel(w, 16, trim="crimson2"), 0, 0)
    blit(img, text(name, fill="cream2"), 4, 2)
    blit(img, bar(w - 8, frac, ghost, kind), 4, 9)
    return img


def hero_plate(portrait, name, hp, hp_max, mp, mp_max, hp_ghost=None, mp_ghost=None, active=False):
    w, h = 108, 34
    img = panel(w, h, trim="gold3" if active else "gold2")
    frame = canvas(26, 26)
    rect(frame, 0, 0, 26, 26, "ink"); rect(frame, 1, 1, 24, 24, "gold1"); rect(frame, 2, 2, 22, 22, "night2")
    if portrait is not None:
        blit(frame, portrait, 2, 2)
    blit(img, frame, 4, 4)
    blit(img, text(name, fill="cream2"), 33, 3)
    blit(img, text("HP", fill="moss5"), 33, 11)
    blit(img, bar(44, hp / hp_max, None if hp_ghost is None else hp_ghost / hp_max,
                  "hp" if hp / hp_max > 0.3 else "low"), 45, 12)
    blit(img, text("MP", fill="glow1"), 33, 20)
    blit(img, bar(44, mp / mp_max, None if mp_ghost is None else mp_ghost / mp_max, "mp"), 45, 21)
    num = text(f"{int(hp)}/{hp_max}", fill="cream1", outline=None)
    blit(img, num, w - 5 - num.shape[1], 26)
    return img


MENU = [("sword", "ATTACK"), ("star", "SKILL"), ("bag", "ITEM"), ("shield", "GUARD")]


def menu(items=MENU, sel=0, frame=0, w=64, title=None):
    rows = len(items)
    h = 6 + rows * 11 + (8 if title else 0)
    img = panel(w, h)
    y0 = 4
    if title:
        blit(img, text(title, fill="gold3"), 5, 2); y0 += 8
    for i, (ic, label) in enumerate(items):
        y = y0 + i * 11
        if i == sel:
            rect(img, 3, y - 1, w - 6, 11, "night3")
            rect(img, 3, y - 1, w - 6, 1, "stone1")
        blit(img, icon(ic), 5, y)
        blit(img, text(label, fill="fire5" if i == sel else "cream1"), 16, y + 1)
    return img


def banner(msg, w=None):
    t = text(msg, fill="cream2")
    w = w or t.shape[1] + 14
    img = panel(w, 13, trim="stone3", fill="night0", top="night1")
    blit(img, t, (w - t.shape[1]) // 2, 3)
    return img


if __name__ == "__main__":
    from px import save, OUT
    s = canvas(320, 180); s[:] = C["stone1"]
    blit(s, hero_plate(None, "KESTREL", 142, 150, 18, 30, hp_ghost=150, active=True), 4, 142)
    blit(s, name_plate("GLOOMLURE", 0.55, 0.7), 228, 4)
    blit(s, menu(sel=1), 120, 60)
    blit(s, menu([("sun", "DAWN CLEAVE"), ("moon", "MOONSTEP")], sel=0, w=86, title="SKILL"), 190, 60)
    for i, k in enumerate(("sword", "sun", "sun")):
        blit(s, lock_plate(k, "whole" if i else "crack"), 230 + i * 15, 26)
    blit(s, lock_plate("sun", "gone", 1), 275, 26)
    blit(s, cursor(), 112, 72)
    blit(s, banner("GLOOMLURE IS GATHERING LIGHT..."), 90, 4)
    blit(s, text("PERFECT!", BIG, fill=["fire5", "fire4", "fire3"], shade="fire2"), 40, 30)
    blit(s, text("21", BIG, fill=["cream2", "cream1"], shade="cream0"), 60, 45)
    save(s, OUT / "ui_sheet.png", s=3)
