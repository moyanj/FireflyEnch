from typing import Tuple, Optional
import hashlib
from PIL import Image as PILImage
from PIL import ImageOps
import imagehash
from io import BytesIO
from PIL import Image as PILImage
from PIL import ImageOps
import imagehash
from io import BytesIO


def compute_quick_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def compute_perceptual_hash(content: bytes) -> imagehash.ImageHash:
    with PILImage.open(BytesIO(content)) as image:
        image = ImageOps.exif_transpose(image)

    return imagehash.phash(image)


def compute_hash(content: bytes) -> Tuple[str, str]:
    return (
        compute_quick_hash(content),
        str(compute_perceptual_hash(content)),
    )


def phash_distance(a: imagehash.ImageHash, b: imagehash.ImageHash) -> int:
    return int(a - b)
