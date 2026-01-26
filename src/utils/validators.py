from pydantic import FilePath
from typing import Any


def ensure_list(value: Any) -> list:
    return [value]


def is_file_image(path: FilePath) -> bool:
    """Check whether a file is an image"""
    # Input checks
    check = path.suffix in [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"]
    return check


def image2bytes(path: FilePath, max_size: int = 1024) -> bytes:
    """
    Convert an image to bytes

    Parameters
    ----------
    path : Path
        Path to the image
    max_size : int, optional
        Maximum size of the image, by default 1024

    Returns
    -------
    bytes
        Bytes of the image
    """
    from PIL import Image
    import numpy as np
    from io import BytesIO

    # Check the image is an image
    assert is_file_image(path), f"{path} is not an image"
    # Read the image
    img = Image.open(path)
    # Resize the image if it exceeds the maximum size
    size = np.array(img.size)
    pixels_max = size.max
    if pixels_max > max_size:
        scale = max_size / pixels_max
        img = img.resize((size * scale).astype(int))
    # Convert to bytes
    buffer = BytesIO()
    img.save(buffer, Image.EXTENSION[path.suffix])
    buffer.seek(0)
    raw = buffer.read()

    return raw
