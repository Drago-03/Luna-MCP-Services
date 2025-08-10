# moved from subdirectory
import io
import base64
import httpx
from PIL import Image

def _to_b64(png_bytes: bytes) -> str:
    return base64.b64encode(png_bytes).decode("ascii")

async def fetch_and_bw(image_url: str, timeout: int = 20) -> str:
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(image_url)
        r.raise_for_status()
        raw = r.content
    with Image.open(io.BytesIO(raw)) as img:
        gray = img.convert("L")
        buf = io.BytesIO()
        gray.save(buf, format="PNG", optimize=True)
        return _to_b64(buf.getvalue())
