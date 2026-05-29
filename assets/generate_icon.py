"""Run directly to preview/regenerate the icon: python assets/generate_icon.py"""
from PIL import Image, ImageDraw


def make_mouse_icon(wheel_color: str = "#22c55e", size: int = 256) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # ── proportional helpers ───────────────────────────────────────────────
    def p(v):  # scale a value designed at 256px
        return int(v * size / 256)

    cx = size // 2

    # ── drop shadow ────────────────────────────────────────────────────────
    sw = p(6)
    d.rounded_rectangle(
        [p(64 + sw), p(24 + sw), p(192 + sw), p(232 + sw)],
        radius=p(56), fill=(0, 0, 0, 55),
    )

    # ── main body ─────────────────────────────────────────────────────────
    body = [p(64), p(24), p(192), p(232)]
    d.rounded_rectangle(body, radius=p(56), fill="#1e1e2e", outline="#3a3a5c", width=p(2))

    # ── button zone (top portion, slightly lighter) ────────────────────────
    btn_bottom = p(112)
    btn_zone = [p(64), p(24), p(192), btn_bottom]
    d.rounded_rectangle(btn_zone, radius=p(56), fill="#2a2a3e", outline="#3a3a5c", width=p(2))
    # flat bottom edge of button zone
    d.rectangle([p(66), btn_bottom - p(56), p(190), btn_bottom], fill="#2a2a3e")

    # ── divider lines ──────────────────────────────────────────────────────
    line_color = "#3a3a5c"
    # horizontal (buttons ↔ palm)
    d.line([(p(66), btn_bottom), (p(190), btn_bottom)], fill=line_color, width=p(2))
    # vertical (left ↔ right button)
    d.line([(cx, p(26)), (cx, btn_bottom - p(2))], fill=line_color, width=p(2))

    # ── scroll wheel ───────────────────────────────────────────────────────
    ww, wh = p(22), p(44)
    wx = cx - ww // 2
    wy = p(38)
    d.rounded_rectangle([wx, wy, wx + ww, wy + wh], radius=p(10), fill=wheel_color)

    return img


def make_ico(path) -> None:
    """Generate a multi-size .ico file for Windows (16, 32, 48, 64, 128, 256px)."""
    import pathlib
    sizes = [16, 32, 48, 64, 128, 256]
    base = make_mouse_icon("#22c55e", size=256)
    frames = [base.resize((s, s), Image.LANCZOS) for s in sizes]
    frames[-1].save(
        pathlib.Path(path),
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[:-1],
    )


if __name__ == "__main__":
    import pathlib

    assets = pathlib.Path(__file__).parent

    # PNG for macOS dock
    png_out = assets / "icon.png"
    make_mouse_icon("#22c55e").save(png_out)
    print(f"Saved {png_out}")

    # ICO for Windows
    ico_out = assets / "icon.ico"
    make_ico(ico_out)
    print(f"Saved {ico_out}")

    # Preview all three states side by side
    preview = Image.new("RGBA", (256 * 3 + 40, 256 + 20), (40, 40, 40, 255))
    for i, color in enumerate(["#22c55e", "#eab308", "#6b7280"]):
        img = make_mouse_icon(color)
        preview.paste(img, (i * 256 + (i + 1) * 10, 10), mask=img)
    preview.save(assets / "icon_preview.png")
    print(f"Saved {assets / 'icon_preview.png'}")
