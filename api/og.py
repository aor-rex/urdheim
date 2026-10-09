"""Share thumbnails, rendered server-side with Pillow.

next/og proved unreliable in the prod container (instant 502s on every
dynamic image route while identical code renders locally), so coin and
profile cards render here instead: deterministic, no JS, always 200.
"""
import io
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
BG = (12, 10, 8)
GOLD = (201, 162, 39)
CREAM = (242, 234, 214)
DIM = (90, 79, 53)
FAINT = (138, 127, 99)
GREEN = (127, 176, 105)
RED = (193, 68, 60)
LINE = (43, 37, 25)

_FONTS = {}


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    key = (name, size)
    if key not in _FONTS:
        base = os.path.join(os.path.dirname(__file__), "..",
                            "web-next", "app", "og-fonts", name)
        _FONTS[key] = ImageFont.truetype(base, size)
    return _FONTS[key]


def fmt_mcap(n) -> str:
    try:
        n = float(n or 0)
    except (TypeError, ValueError):
        return "$0"
    if n >= 1_000_000_000:
        return f"${n / 1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"${n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"${n / 1_000:.1f}".replace(".0K", "K") + "K"
    return f"${round(n)}"


def _base() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 6], fill=GOLD)
    d.rectangle([0, H - 6, W, H], fill=GOLD)
    return img, d


def _eyebrow(d: ImageDraw.ImageDraw, text: str) -> None:
    f = _font("LiberationSans-Regular.ttf", 24)
    tracking = 12
    tw = sum(d.textlength(ch, font=f) for ch in text) + tracking * (len(text) - 1)
    x = (W - tw) / 2
    for ch in text:
        d.text((x, 84), ch, font=f, fill=DIM)
        x += d.textlength(ch, font=f) + tracking


def _stat(d: ImageDraw.ImageDraw, x: int, value: str, label: str,
          color=CREAM, vsize: int = 56) -> None:
    vf = _font("Gelasio-Regular.ttf", vsize)
    lf = _font("LiberationSans-Regular.ttf", 20)
    d.text((x, 268), value, font=vf, fill=color)
    lx = x
    for ch in label:
        d.text((lx, 348), ch, font=lf, fill=DIM)
        lx += d.textlength(ch, font=lf) + 5


def png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def coin_card(ticker: str, seal: str, delta: str, peak, now,
              callers: int, mint: str) -> bytes:
    img, d = _base()
    _eyebrow(d, "URDHEIM · SHILL RECEIPT")
    tick = "$" + (ticker or "UNKNOWN")[:14]
    tsize = 88
    while tsize > 40:
        f = _font("Gelasio-Regular.ttf", tsize)
        if d.textlength(tick, font=f) <= 480:
            break
        tsize -= 8
    d.text((120, 200), tick, font=_font("Gelasio-Regular.ttf", tsize), fill=CREAM)
    seal_c = RED if seal == "RUGGED" else GOLD
    d.text((124, 330), f"{seal} {delta or ''}".strip(),
           font=_font("LiberationSans-Regular.ttf", 28), fill=seal_c)
    d.line([640, 190, 640, 430], fill=LINE, width=2)
    down = bool(now and peak and now < peak)
    _stat(d, 670, fmt_mcap(peak), "PEAK MCAP", vsize=44)
    _stat(d, 870, fmt_mcap(now), "NOW MCAP", RED if down else GREEN, vsize=44)
    _stat(d, 1070, str(callers), "CALLER" if callers == 1 else "CALLERS",
          GOLD, vsize=44)
    foot = _font("LiberationSans-Regular.ttf", 22)
    tail = (mint[:18] + "..." + mint[-6:]) if mint and len(mint) > 26 else (mint or "")
    ft = f"{tail} · urdheim.zone.id"
    d.text(((W - d.textlength(ft, font=foot)) / 2, 520), ft, font=foot, fill=FAINT)
    return png(img)


def profile_card(handle: str, name: str, filed: int, scored: int,
                 avg: int) -> bytes:
    img, d = _base()
    _eyebrow(d, "URDHEIM · PUBLIC RECORD")
    cx, cy, r = 200, 300, 62
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GOLD, width=4)
    initial = (handle[:1] or "?").upper()
    f = _font("Gelasio-Regular.ttf", 56)
    d.text((cx - d.textlength(initial, font=f) / 2, cy - 40),
           initial, font=f, fill=GOLD)
    nm = (name or "@" + handle)[:24]
    nsize = 54
    while nsize > 30:
        f = _font("Gelasio-Italic.ttf", nsize)
        if d.textlength(nm, font=f) <= 320:
            break
        nsize -= 6
    d.text((300, 230), nm, font=_font("Gelasio-Italic.ttf", nsize), fill=CREAM)
    d.text((302, 300), ("@" + handle)[:24],
           font=_font("LiberationSans-Regular.ttf", 26), fill=FAINT)
    d.line([640, 190, 640, 430], fill=LINE, width=2)
    avg_c = GREEN if (avg or 0) > 0 else (RED if (avg or 0) < 0 else CREAM)
    asign = "+" if (avg or 0) > 0 else ""
    _stat(d, 690, str(filed or 0), "FILED")
    _stat(d, 860, str(scored or 0), "SCORED")
    _stat(d, 1010, f"{asign}{avg or 0}%", "AVG RETURN", avg_c, vsize=44)
    return png(img)
