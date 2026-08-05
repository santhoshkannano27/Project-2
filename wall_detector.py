"""
wall_detector.py

Turns a 2D architectural blueprint / floor-plan image into a binary
"wall mask": 1 where a wall exists, 0 for open floor space.

Assumes the blueprint is drawn as dark lines/walls on a light background
(the standard convention for floor plans and CAD/PDF exports). If yours
is inverted (light lines on a dark background), pass invert=True.
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter


def load_wall_mask(
    image: Image.Image,
    threshold: int = 200,
    invert: bool = False,
    thicken: int = 1,
) -> np.ndarray:
    """
    Args:
        image: source blueprint image (any mode; converted to grayscale).
        threshold: grayscale cutoff (0-255). Pixels darker than this count
            as "wall" (lighter, if invert=True). Lower it if faint wall
            lines are being missed; raise it if furniture/text/dimension
            lines are wrongly picked up as walls.
        invert: True if walls are drawn light-on-dark instead of the usual
            dark-on-light.
        thicken: how many 1px dilation passes to run, to close small gaps
            in hand-drawn or low-resolution line work so walls form solid
            shapes rather than thin single-pixel outlines. 0 = off.

    Returns:
        (H, W) uint8 array: 1 = wall, 0 = open space.
    """
    gray = image.convert("L")
    arr = np.asarray(gray, dtype=np.uint8)

    if invert:
        mask = (arr > threshold).astype(np.uint8)
    else:
        mask = (arr < threshold).astype(np.uint8)

    if thicken > 0:
        mask_img = Image.fromarray(mask * 255)
        for _ in range(thicken):
            mask_img = mask_img.filter(ImageFilter.MaxFilter(3))
        mask = (np.asarray(mask_img) > 127).astype(np.uint8)

    return mask


def wall_coverage_ratio(mask: np.ndarray) -> float:
    """Fraction of pixels classified as wall. Useful as a sanity check —
    if this is near 0.0 or near 1.0, your threshold/invert settings are
    probably wrong for this image."""
    return float(mask.mean())
