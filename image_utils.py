import uuid
from PIL import Image,ImageOps
from io import BytesIO
from pathlib import Path

PROFILE_PICS_DIR = Path("media/profile_pics")


def process_profile_picture(content: bytes) -> str:
    with Image.open(BytesIO(content)) as original:
        image = ImageOps.exif_transpose(original)  # Correct orientation based on EXIF data
        image = ImageOps.fit(image, (300, 300), method=Image.LANCZOS)  # Resize to fit within 300x300
    
    if image.mode in ("RGBA", "P", "LA"):
        image = image.convert("RGB")  # Convert to RGB if image has alpha channel

    filename = f"{uuid.uuid4().hex}.jpg"
    file_path = PROFILE_PICS_DIR / filename
    PROFILE_PICS_DIR.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
    image.save(file_path, format="JPEG", quality=85, optimize=True)  # Save as JPEG with good quality
    return filename

def delete_profile_image(filename: str |None ) -> None:
    if not filename:
        return
    file_path = PROFILE_PICS_DIR / filename
    if file_path.exists():
        file_path.unlink()