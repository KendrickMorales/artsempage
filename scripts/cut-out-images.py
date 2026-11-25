"""Cut every site image out of its background, so they all sit on the page's paper colour.

    python3 -m venv .venv && .venv/bin/pip install "rembg[cpu]" pillow
    .venv/bin/python scripts/cut-out-images.py

Reads assets/web/*.jpg and writes a transparent assets/web/*.webp beside each one. The "Other
fabrication" parts keep their JPEGs, white ground and all, so they are not listed here.

The white-ground renders (scans, CAD, the sketch) are keyed out by colour, which keeps every thin
tube; an AI model would round them off. The shop photos have no plain background to key, so they
go through rembg's BiRefNet models (about 1 GB each, downloaded on first run to ~/.rembg).
"""

from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

WEB = Path(__file__).resolve().parent.parent / "assets" / "web"

# White renders keyed by colour. Interior white regions larger than this share of the image
# (the windows of a scanned shell) are background too; smaller ones are highlights on the part.
WHITE_RENDERS = ["cup-scan", "e90-scan", "porsche-scan"]
HOLE_SHARE = 0.0008

# Shop photos, and the model that separated each one best. birefnet-general lost most of the
# white FRS against the white garage behind it; birefnet-dis kept the cage and the A-pillar.
PHOTOS = {
    "e90-build": "birefnet-general",
    "track-build": "birefnet-general",
    "ls-mount": "birefnet-general",
    "frs-build": "birefnet-dis",
}

# Photos looking into the car through a door or window. The model treats what it sees through the
# openings as background, so everything inside the car's outline is filled back in.
FILL_INSIDE = {"e90-build", "frs-build"}

# A landscape band of a portrait photo, as fractions of its height, for the hero's scan-to-build
# wipe. The E90's keeps the main hoop and the door bars and drops the sill.
WIDE_CROPS = {"e90-build": (0.06, 0.66)}


def key_out_white(rgb: np.ndarray) -> np.ndarray:
    """Alpha for a render on white: transparent background, soft anti-aliased edge, no halo."""
    darkness = 255 - rgb.min(axis=2).astype(np.int16)  # 0 on pure white
    near_white = darkness < 22
    labels, count = ndimage.label(near_white)  # 4-connected
    height, width = near_white.shape
    areas = np.bincount(labels.ravel(), minlength=count + 1)
    on_edge = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    is_background = areas > HOLE_SHARE * width * height
    is_background[on_edge] = True
    is_background[0] = False  # label 0 is everything that isn't near white
    background = is_background[labels]
    alpha = np.where(background, 0, 255).astype(np.float32)
    # Across a 2px band on the boundary, take opacity from how far the pixel is from white.
    band = ndimage.binary_dilation(background, iterations=2) & ~background
    soft = np.clip(darkness.astype(np.float32) / 60.0, 0, 1) * 255
    alpha[band] = soft[band]
    return alpha.astype(np.uint8)


def unmix_white(rgb: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Remove the white an edge pixel was blended with, so it doesn't glow on the paper."""
    a = alpha.astype(np.float32)[..., None] / 255.0
    safe = np.maximum(a, 1 / 255)
    clean = (rgb.astype(np.float32) - (1 - a) * 255) / safe
    return np.clip(np.where(a > 0, clean, rgb), 0, 255).astype(np.uint8)


def save(rgba: Image.Image, name: str) -> None:
    # Trim the empty margin so layouts size the part itself; near-invisible haze doesn't count.
    rgba = rgba.crop(rgba.getchannel("A").point(lambda v: 255 if v > 16 else 0).getbbox())
    rgba.save(WEB / f"{name}.webp", "WEBP", quality=86, method=6)
    print(f"{name}.webp  {rgba.width}x{rgba.height}")


def main() -> None:
    for name in WHITE_RENDERS:
        rgb = np.asarray(Image.open(WEB / f"{name}.jpg").convert("RGB"))
        alpha = key_out_white(rgb)
        save(Image.fromarray(np.dstack([unmix_white(rgb, alpha), alpha]), "RGBA"), name)

    # The sketch already exists as a transparent PNG; use it rather than keying the JPEG.
    sketch = Image.open(WEB.parent / "clownshoe.png").convert("RGBA")
    sketch.thumbnail((1200, 1200))
    save(sketch, "z3-sketch")

    from rembg import new_session, remove  # imported late: slow, and only the photos need it

    sessions: dict[str, object] = {}
    for name, model in PHOTOS.items():
        session = sessions.setdefault(model, new_session(model))
        photo = Image.open(WEB / f"{name}.jpg").convert("RGB")
        # Keep only the model's mask: it blanks the colour under what it removes, and the
        # interior fill below brings some of that back.
        cut = photo.copy()
        cut.putalpha(remove(photo, session=session, only_mask=True))
        cut = drop_specks(cut)
        if name in FILL_INSIDE:
            cut = fill_inside(cut)
        save(fade_frame_edges(cut), name)
        if name in WIDE_CROPS:
            top, bottom = WIDE_CROPS[name]
            wide = cut.crop((0, int(top * cut.height), cut.width, int(bottom * cut.height)))
            save(fade_frame_edges(wide), f"{name}-wide")


def fill_inside(rgba: Image.Image, reach: float = 0.03) -> Image.Image:
    """Make the whole car opaque: close gaps narrower than `reach` of the image, fill the holes."""
    pixels = np.array(rgba)
    alpha = pixels[..., 3]
    radius = int(reach * max(alpha.shape))
    padded = np.pad(alpha > 128, radius)
    closed = ndimage.binary_closing(padded, iterations=radius)[radius:-radius, radius:-radius]
    inside = ndimage.binary_erosion(ndimage.binary_fill_holes(closed), iterations=3)
    pixels[..., 3] = np.where(inside, 255, alpha)  # the model's soft outer edge stays
    return Image.fromarray(pixels, "RGBA")


def fade_frame_edges(rgba: Image.Image, share: float = 0.07) -> Image.Image:
    """Fade the car out where the photo's frame cut through it, instead of a ruler-straight edge."""
    pixels = np.array(rgba).astype(np.float32)
    height, width = pixels.shape[:2]
    reach = share * max(width, height)
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float32)
    distance = np.minimum.reduce([xs, ys, width - 1 - xs, height - 1 - ys])
    pixels[..., 3] *= np.clip(distance / reach, 0, 1) ** 0.8
    return Image.fromarray(pixels.astype(np.uint8), "RGBA")


def drop_specks(rgba: Image.Image) -> Image.Image:
    """Clear stray fragments the model kept from the shop behind (under 0.5% of the image)."""
    pixels = np.array(rgba)
    labels, count = ndimage.label(pixels[..., 3] > 16)
    areas = np.bincount(labels.ravel(), minlength=count + 1)
    speck = areas < 0.005 * labels.size
    speck[0] = False
    pixels[speck[labels] | (pixels[..., 3] <= 16), 3] = 0
    return Image.fromarray(pixels, "RGBA")


if __name__ == "__main__":
    main()
