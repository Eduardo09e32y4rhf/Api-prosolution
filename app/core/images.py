"""Validação e preparo de imagens para o feed do Instagram.

A Graph API só publica JPEG, aceita proporções entre 4:5 e 1.91:1 e imagens de até 8 MB.
Tudo que o usuário envia passa por aqui: a imagem é decodificada de verdade (não confiamos em
extensão nem em Content-Type), corrigida, recortada e regravada como JPEG sem metadados.
"""

import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_FORMATS = {"JPEG", "PNG"}
MIN_WIDTH = 320  # mínimo exigido pelo Instagram
MAX_WIDTH = 1440  # largura máxima útil no feed; acima disso só pesa
MIN_RATIO = 4 / 5  # retrato 4:5
MAX_RATIO = 1.91  # paisagem 1.91:1
MAX_PIXELS = 40_000_000  # protege contra "bombas de descompressão"
JPEG_QUALITY = 90

# Pillow também recusa imagens muito acima disto (DecompressionBombError)
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


class InvalidImageError(ValueError):
    """Imagem recusada. A mensagem é segura para mostrar ao usuário."""


@dataclass(frozen=True)
class ProcessedImage:
    data: bytes
    width: int
    height: int
    cropped: bool  # True quando a proporção original foi ajustada


def process_image(raw: bytes, max_bytes: int) -> ProcessedImage:
    if not raw:
        raise InvalidImageError("O arquivo está vazio.")
    if len(raw) > max_bytes:
        raise InvalidImageError(f"A imagem tem mais de {max_bytes // (1024 * 1024)} MB.")

    try:
        with Image.open(io.BytesIO(raw)) as probe:
            fmt = probe.format
            width, height = probe.size
        if fmt not in ALLOWED_FORMATS:
            raise InvalidImageError("Formato não suportado. Envie uma imagem JPEG ou PNG.")
        if width * height > MAX_PIXELS:
            raise InvalidImageError("A imagem é grande demais. Reduza a resolução e tente de novo.")

        with Image.open(io.BytesIO(raw)) as img:
            img.load()
            image = ImageOps.exif_transpose(img)  # respeita a orientação do celular
            image = _to_rgb(image)
    except InvalidImageError:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError, ValueError) as exc:
        raise InvalidImageError("Não foi possível ler a imagem. Envie um arquivo JPEG ou PNG válido.") from exc

    if image.width < MIN_WIDTH:
        raise InvalidImageError(f"A imagem é pequena demais (mínimo de {MIN_WIDTH} pixels de largura).")

    image, cropped = _fit_ratio(image)
    if image.width > MAX_WIDTH:
        new_height = round(image.height * MAX_WIDTH / image.width)
        image = image.resize((MAX_WIDTH, new_height), Image.Resampling.LANCZOS)

    out = io.BytesIO()
    # Sem exif/icc: remove GPS e outros metadados pessoais do arquivo publicado
    image.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    data = out.getvalue()
    if len(data) > max_bytes:
        raise InvalidImageError("Mesmo depois de otimizada a imagem passa do limite. Envie uma menor.")
    return ProcessedImage(data=data, width=image.width, height=image.height, cropped=cropped)


def _to_rgb(image: Image.Image) -> Image.Image:
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))  # JPEG não tem transparência
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")


def _fit_ratio(image: Image.Image) -> tuple[Image.Image, bool]:
    """Recorta (pelo centro) o mínimo necessário para entrar na faixa de proporção do Instagram."""
    width, height = image.size
    ratio = width / height
    if ratio > MAX_RATIO:
        new_width = int(height * MAX_RATIO)
        left = (width - new_width) // 2
        return image.crop((left, 0, left + new_width, height)), True
    if ratio < MIN_RATIO:
        new_height = int(width / MIN_RATIO)
        top = (height - new_height) // 2
        return image.crop((0, top, width, top + new_height)), True
    return image, False
