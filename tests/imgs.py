"""Gera imagens de teste em memória."""

import io

from PIL import Image


def make_image(
    width: int, height: int, fmt: str = "JPEG", mode: str = "RGB", color=(200, 30, 30), **save_kwargs
) -> bytes:
    img = Image.new(mode, (width, height), color)
    out = io.BytesIO()
    img.save(out, format=fmt, **save_kwargs)
    return out.getvalue()


def open_image(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data))
    img.load()
    return img
