from pathlib import Path

import qrcode

from app.core.config import get_settings


def generate_qr(data: str, name: str) -> str:
    output_dir = get_settings().data_dir / "qr"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{name}.png"
    img = qrcode.make(data)
    img.save(path)
    return str(path)
