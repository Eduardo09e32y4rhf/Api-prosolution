"""Validação e preparo de imagens para o Instagram."""

import io

import pytest
from PIL import Image

from app.core.images import MAX_RATIO, MAX_WIDTH, MIN_RATIO, InvalidImageError, process_image

from .imgs import make_image, open_image

MAX_BYTES = 8 * 1024 * 1024


def test_valid_jpeg_in_range_is_kept_without_crop():
    result = process_image(make_image(1080, 1080), MAX_BYTES)
    assert (result.width, result.height, result.cropped) == (1080, 1080, False)
    assert open_image(result.data).format == "JPEG"


def test_png_with_transparency_becomes_jpeg_on_white_background():
    png = make_image(800, 800, "PNG", "RGBA", color=(255, 0, 0, 0))  # totalmente transparente
    result = process_image(png, MAX_BYTES)
    img = open_image(result.data)
    assert img.format == "JPEG" and img.mode == "RGB"
    r, g, b = img.getpixel((400, 400))
    assert min(r, g, b) > 240, "a transparência deveria virar branco, não preto"


def test_palette_png_with_transparency_is_supported():
    img = Image.new("P", (600, 600))
    img.info["transparency"] = 0
    out = io.BytesIO()
    img.save(out, format="PNG", transparency=0)
    assert open_image(process_image(out.getvalue(), MAX_BYTES).data).format == "JPEG"


@pytest.mark.parametrize(("width", "height"), [(3000, 600), (2000, 1000)])
def test_too_wide_image_is_cropped_to_landscape_limit(width: int, height: int):
    result = process_image(make_image(width, height), MAX_BYTES)
    assert result.cropped
    assert result.width / result.height == pytest.approx(MAX_RATIO, abs=0.01)


def test_too_tall_image_is_cropped_to_portrait_limit():
    result = process_image(make_image(600, 3000), MAX_BYTES)
    assert result.cropped
    assert result.width / result.height == pytest.approx(MIN_RATIO, abs=0.01)


@pytest.mark.parametrize("size", [(1080, 1350), (1080, 566)])  # 4:5 e ~1.91:1 exatos
def test_ratio_limits_are_accepted_as_is(size: tuple[int, int]):
    assert not process_image(make_image(*size), MAX_BYTES).cropped


def test_crop_keeps_the_center():
    img = Image.new("RGB", (3000, 600), (0, 0, 255))
    img.paste((255, 0, 0), (1400, 0, 1600, 600))  # faixa vermelha no centro
    out = io.BytesIO()
    img.save(out, format="PNG")
    result = open_image(process_image(out.getvalue(), MAX_BYTES).data)
    assert result.getpixel((result.width // 2, result.height // 2))[0] > 200, "o centro deveria ser preservado"
    assert result.getpixel((5, result.height // 2))[2] > 200, "as bordas é que são cortadas"


def test_large_image_is_downscaled():
    result = process_image(make_image(4000, 4000), MAX_BYTES)
    assert (result.width, result.height) == (MAX_WIDTH, MAX_WIDTH)
    assert len(result.data) < 2 * 1024 * 1024


def test_exif_orientation_is_applied_and_metadata_removed():
    img = Image.new("RGB", (1000, 500), (10, 10, 10))
    exif = Image.Exif()
    exif[0x0112] = 6  # gira 90° para exibir
    exif[0x010F] = "CameraMarca"
    exif[0x8825] = {1: "S", 2: (23.0, 33.0, 0.0)}  # bloco GPS
    out = io.BytesIO()
    img.save(out, format="JPEG", exif=exif)

    result = process_image(out.getvalue(), MAX_BYTES)
    processed = open_image(result.data)
    assert (processed.width, processed.height) == (500 * 1, 1000) or processed.height > processed.width
    assert not processed.getexif(), "nenhum metadado EXIF (como GPS) deveria sobrar"
    assert b"CameraMarca" not in result.data and b"Exif" not in result.data


@pytest.mark.parametrize("size", [(200, 200), (319, 400)])
def test_too_small_is_rejected(size: tuple[int, int]):
    with pytest.raises(InvalidImageError, match="pequena demais"):
        process_image(make_image(*size), MAX_BYTES)


@pytest.mark.parametrize("fmt", ["GIF", "WEBP", "BMP", "TIFF"])
def test_other_formats_are_rejected(fmt: str):
    with pytest.raises(InvalidImageError, match="Formato não suportado"):
        process_image(make_image(800, 800, fmt), MAX_BYTES)


@pytest.mark.parametrize(
    "payload",
    [b"", b"isto nao e uma imagem", b"<script>alert(1)</script>", b"\xff\xd8\xff\xe0" + b"corrompido" * 50],
    ids=["vazio", "texto", "html", "jpeg-truncado"],
)
def test_garbage_is_rejected(payload: bytes):
    with pytest.raises(InvalidImageError):
        process_image(payload, MAX_BYTES)


def test_svg_is_rejected():
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="500" height="500"><script>alert(1)</script></svg>'
    with pytest.raises(InvalidImageError):
        process_image(svg, MAX_BYTES)


def test_file_over_size_limit_is_rejected():
    big = make_image(800, 800) + b"\0" * (MAX_BYTES + 1)
    with pytest.raises(InvalidImageError, match="mais de 8 MB"):
        process_image(big, MAX_BYTES)


def test_decompression_bomb_is_rejected():
    """PNG de 1 bit com 20 mil x 20 mil pixels (400 MP): poucos KB no disco, centenas de MB decodificado."""
    bomb = Image.new("1", (20_000, 20_000))
    out = io.BytesIO()
    bomb.save(out, format="PNG")
    assert len(out.getvalue()) < MAX_BYTES, "o ataque só faz sentido se o arquivo for pequeno"
    with pytest.raises(InvalidImageError):
        process_image(out.getvalue(), MAX_BYTES)


def test_polyglot_jpeg_with_appended_script_is_neutralised():
    """Arquivo que é JPEG válido com HTML anexado: o resultado é regravado, o anexo desaparece."""
    polyglot = make_image(800, 800) + b"<script>alert(1)</script>"
    result = process_image(polyglot, MAX_BYTES)
    assert b"<script>" not in result.data
