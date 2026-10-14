"""앱 아이콘 생성: assets/icon.png (1024px) 와 assets/icon.icns 를 만든다.

    python3 tools/make_icon.py

Pillow 필요. 글꼴은 Inter Bold (없으면 DejaVu Sans Bold).
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

S = 4  # 슈퍼샘플링 배율
N = 1024 * S
OUT = Path(__file__).resolve().parent.parent / "assets"

FONTS = [
    "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def font(size: int) -> ImageFont.FreeTypeFont:
    for f in FONTS:
        if Path(f).exists():
            return ImageFont.truetype(f, size * S)
    return ImageFont.load_default()


def gradient(size, top, bottom) -> Image.Image:
    g = Image.new("RGB", (1, size))
    for y in range(size):
        t = y / (size - 1)
        g.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)))
    return g.resize((size, size))


def card(w, h, color, label, label_color, radius=60) -> Image.Image:
    """사진 카드 한 장(그림자 포함) 반환."""
    w, h, radius = w * S, h * S, radius * S
    pad = 60 * S
    img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (pad, pad + 24 * S, pad + w, pad + h + 24 * S), radius, fill=(0, 0, 0, 120)
    )
    from PIL import ImageFilter

    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(28 * S)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((pad, pad, pad + w, pad + h), radius, fill=color)
    # 사진 느낌: 위쪽 하늘 + 산 실루엣 + 해
    inner = (pad + 28 * S, pad + 28 * S, pad + w - 28 * S, pad + h - 118 * S)
    d.rounded_rectangle(inner, 36 * S, fill=label_color[0])
    ix0, iy0, ix1, iy1 = inner
    d.polygon(
        [(ix0, iy1), (ix0 + (ix1 - ix0) * 0.35, iy0 + (iy1 - iy0) * 0.45),
         (ix0 + (ix1 - ix0) * 0.55, iy0 + (iy1 - iy0) * 0.75),
         (ix0 + (ix1 - ix0) * 0.75, iy0 + (iy1 - iy0) * 0.35), (ix1, iy1)],
        fill=label_color[1],
    )
    # 모서리 둥글게 마스크
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(inner, 36 * S, fill=255)
    clipped = Image.new("RGBA", img.size, (0, 0, 0, 0))
    clipped.paste(img.crop((0, 0, *img.size)), (0, 0), mask)
    base = img.copy()
    ImageDraw.Draw(base).rounded_rectangle(inner, 36 * S, fill=label_color[0])
    base.alpha_composite(clipped)
    d = ImageDraw.Draw(base)
    d.ellipse((ix1 - 150 * S, iy0 + 30 * S, ix1 - 70 * S, iy0 + 110 * S), fill=(255, 255, 255, 230))
    f = font(84)
    tw = d.textlength(label, font=f)
    d.text((pad + (w - tw) / 2, pad + h - 100 * S), label, font=f, fill=label_color[2])
    return base


def main() -> None:
    OUT.mkdir(exist_ok=True)
    # 앱 아이콘 본체: 맥 규격에 맞춰 사방 100px 여백, 모서리 둥근 사각형
    m, r = 100 * S, 185 * S
    bg = gradient(N, (38, 70, 83), (18, 28, 48)).convert("RGBA")
    mask = Image.new("L", (N, N), 0)
    ImageDraw.Draw(mask).rounded_rectangle((m, m, N - m, N - m), r, fill=255)
    icon = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    icon.paste(bg, (0, 0), mask)

    raw = card(420, 510, (255, 255, 255, 255), "RAW", ((255, 183, 77), (230, 120, 40), (200, 90, 20)))
    jpg = card(420, 510, (255, 255, 255, 255), "JPG", ((144, 202, 249), (66, 120, 190), (30, 70, 140)))
    raw = raw.rotate(9, resample=Image.BICUBIC, expand=True)
    jpg = jpg.rotate(-8, resample=Image.BICUBIC, expand=True)
    icon.alpha_composite(raw, (N // 2 - raw.width // 2 + 125 * S, N // 2 - raw.height // 2 + 55 * S))
    icon.alpha_composite(jpg, (N // 2 - jpg.width // 2 - 125 * S, N // 2 - jpg.height // 2 - 45 * S))

    icon = icon.resize((1024, 1024), Image.LANCZOS)
    icon.save(OUT / "icon.png")
    icon.save(OUT / "icon.icns", sizes=[(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024)])
    print("saved", OUT)


if __name__ == "__main__":
    main()
