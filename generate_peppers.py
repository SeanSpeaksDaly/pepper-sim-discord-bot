"""Generate tiny pixel art pepper sprites in Stardew Valley style.

Two base shapes:
  - "round" bell pepper shape (used by Green and Yellow)
  - "long" chili pepper shape (used by Red and Golden)
"""
from PIL import Image, ImageDraw


def draw_round_pepper(filename, body_colors, stem_color=(34, 120, 15), highlight_color=None, sparkle=False):
    """Draw a round bell-pepper style sprite (Green / Yellow shape)."""
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    dark, mid, light = body_colors
    if highlight_color is None:
        highlight_color = light
    outline = (40, 30, 20, 200)

    # Stem
    draw.rectangle([14, 2, 17, 6], fill=stem_color)
    draw.rectangle([13, 4, 14, 5], fill=(28, 100, 12))

    # Body — wide, round bell pepper
    draw.rectangle([10, 7, 21, 22], fill=mid)
    draw.rectangle([9, 9, 22, 20], fill=mid)
    draw.rectangle([11, 6, 20, 8], fill=mid)
    # Flat-ish bottom with bumps (bell pepper lobes)
    draw.rectangle([10, 22, 13, 24], fill=mid)
    draw.rectangle([18, 22, 21, 24], fill=mid)
    draw.rectangle([14, 22, 17, 23], fill=dark)  # indent between lobes

    # Shading — left/bottom darker
    draw.rectangle([9, 9, 10, 20], fill=dark)
    draw.rectangle([10, 20, 12, 22], fill=dark)
    draw.rectangle([10, 7, 11, 9], fill=dark)
    draw.rectangle([10, 22, 11, 24], fill=dark)

    # Highlight — right/top lighter
    draw.rectangle([20, 8, 22, 14], fill=light)
    draw.rectangle([19, 7, 21, 9], fill=light)

    # Shine spot
    draw.rectangle([18, 9, 20, 11], fill=highlight_color)

    # Outline — top
    for x in range(11, 21):
        img.putpixel((x, 5), outline)
    # Stem top
    for x in range(14, 18):
        img.putpixel((x, 1), outline)
    img.putpixel((13, 1), outline)
    img.putpixel((13, 2), outline)
    img.putpixel((13, 3), outline)
    img.putpixel((12, 4), outline)
    img.putpixel((12, 5), outline)
    # Left side
    for y in range(6, 9):
        img.putpixel((9, y), outline)
    for y in range(9, 21):
        img.putpixel((8, y), outline)
    for y in range(21, 25):
        img.putpixel((9, y), outline)
    # Right side
    for y in range(6, 9):
        img.putpixel((21, y), outline)
    for y in range(9, 21):
        img.putpixel((23, y), outline)
    for y in range(21, 25):
        img.putpixel((22, y), outline)
    # Bottom lobes
    for x in range(10, 14):
        img.putpixel((x, 25), outline)
    for x in range(18, 22):
        img.putpixel((x, 25), outline)
    # Bottom middle indent
    img.putpixel((13, 24), outline)
    img.putpixel((14, 23), outline)
    img.putpixel((17, 23), outline)
    img.putpixel((18, 24), outline)

    if sparkle:
        _add_sparkles(img)

    img.save(filename)
    print(f"Created {filename}")


def draw_long_pepper(filename, body_colors, stem_color=(34, 120, 15), highlight_color=None, sparkle=False):
    """Draw a long chili pepper style sprite (Red / Golden shape)."""
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    dark, mid, light = body_colors
    if highlight_color is None:
        highlight_color = light
    outline = (40, 30, 20, 200)

    # Stem — slightly angled
    draw.rectangle([15, 1, 17, 5], fill=stem_color)
    draw.rectangle([14, 3, 15, 5], fill=(28, 100, 12))

    # Body — narrow, elongated chili
    draw.rectangle([13, 5, 19, 8], fill=mid)   # top shoulder
    draw.rectangle([12, 8, 20, 12], fill=mid)   # widest part
    draw.rectangle([11, 12, 19, 16], fill=mid)  # upper mid
    draw.rectangle([10, 16, 18, 20], fill=mid)  # lower mid
    draw.rectangle([9, 20, 16, 23], fill=mid)   # taper
    draw.rectangle([8, 23, 14, 25], fill=mid)   # more taper
    draw.rectangle([7, 25, 11, 27], fill=mid)   # tip area
    draw.rectangle([6, 27, 9, 28], fill=dark)   # very tip

    # Shading — left edge darker
    draw.rectangle([12, 8, 13, 12], fill=dark)
    draw.rectangle([11, 12, 12, 16], fill=dark)
    draw.rectangle([10, 16, 11, 20], fill=dark)
    draw.rectangle([9, 20, 10, 23], fill=dark)
    draw.rectangle([8, 23, 9, 25], fill=dark)
    draw.rectangle([7, 25, 8, 27], fill=dark)

    # Highlight — right side lighter
    draw.rectangle([18, 8, 20, 12], fill=light)
    draw.rectangle([17, 6, 19, 9], fill=light)

    # Shine spot
    draw.rectangle([17, 9, 19, 11], fill=highlight_color)

    # Outline — stem
    for x in range(15, 18):
        img.putpixel((x, 0), outline)
    img.putpixel((14, 1), outline)
    img.putpixel((13, 2), outline)
    img.putpixel((13, 3), outline)
    img.putpixel((13, 4), outline)
    img.putpixel((18, 1), outline)
    img.putpixel((18, 2), outline)
    img.putpixel((18, 3), outline)
    img.putpixel((18, 4), outline)
    # Right side going down
    img.putpixel((20, 5), outline)
    img.putpixel((20, 6), outline)
    img.putpixel((20, 7), outline)
    for y in range(8, 12):
        img.putpixel((21, y), outline)
    for y in range(12, 16):
        img.putpixel((20, y), outline)
    for y in range(16, 20):
        img.putpixel((19, y), outline)
    for y in range(20, 23):
        img.putpixel((17, y), outline)
    for y in range(23, 25):
        img.putpixel((15, y), outline)
    for y in range(25, 27):
        img.putpixel((12, y), outline)
    img.putpixel((10, 27), outline)
    img.putpixel((9, 28), outline)
    # Left side going down
    img.putpixel((12, 5), outline)
    img.putpixel((12, 6), outline)
    img.putpixel((12, 7), outline)
    for y in range(8, 12):
        img.putpixel((11, y), outline)
    for y in range(12, 16):
        img.putpixel((10, y), outline)
    for y in range(16, 20):
        img.putpixel((9, y), outline)
    for y in range(20, 23):
        img.putpixel((8, y), outline)
    for y in range(23, 25):
        img.putpixel((7, y), outline)
    for y in range(25, 27):
        img.putpixel((6, y), outline)
    img.putpixel((5, 27), outline)
    img.putpixel((5, 28), outline)
    # Tip
    for x in range(6, 10):
        img.putpixel((x, 29), outline)

    if sparkle:
        _add_sparkles(img)

    img.save(filename)
    print(f"Created {filename}")


def _add_sparkles(img):
    sparkle_color = (255, 255, 200, 220)
    faint = (255, 255, 255, 120)
    for sx, sy in [(4, 6), (24, 4), (26, 17), (3, 20), (24, 26)]:
        if 0 <= sx < 32 and 0 <= sy < 32:
            img.putpixel((sx, sy), sparkle_color)
        if sx + 1 < 32:
            img.putpixel((sx + 1, sy), faint)
        if sy - 1 >= 0:
            img.putpixel((sx, sy - 1), faint)


# ── Green Pepper — round bell shape, common ──
draw_round_pepper(
    "assets/pepper_green.png",
    body_colors=(
        (30, 100, 30),   # dark green
        (50, 160, 50),   # mid green
        (90, 200, 90),   # light green
    ),
    highlight_color=(140, 230, 140),
)

# ── Red Pepper — long chili shape, uncommon ──
draw_long_pepper(
    "assets/pepper_red.png",
    body_colors=(
        (140, 20, 20),   # dark red
        (210, 45, 45),   # mid red
        (240, 90, 90),   # light red
    ),
    highlight_color=(255, 150, 150),
)

# ── Yellow Pepper — round bell shape (recolor of green), rare ──
draw_round_pepper(
    "assets/pepper_yellow.png",
    body_colors=(
        (180, 140, 10),  # dark yellow
        (240, 200, 30),  # mid yellow
        (255, 230, 80),  # light yellow
    ),
    highlight_color=(255, 245, 160),
)

# ── Golden Pepper — long chili shape (recolor of red), legendary ──
draw_long_pepper(
    "assets/pepper_golden.png",
    body_colors=(
        (180, 130, 20),  # dark gold
        (230, 180, 40),  # mid gold
        (255, 220, 80),  # light gold
    ),
    highlight_color=(255, 250, 180),
    sparkle=True,
)

print("\nAll pepper sprites generated!")
