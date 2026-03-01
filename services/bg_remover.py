import httpx
import base64
from config import config


async def remove_background(image_url: str) -> str:
    """
    Удаляет фон через remove.bg API.
    Returns base64-строку PNG без фона.
    """
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.remove.bg/v1.0/removebg",
            data={
                "image_url": image_url,
                "size": "auto",
                "type": "product",
                "format": "png",
            },
            headers={"X-Api-Key": config.REMOVE_BG_API_KEY},
        )

        if resp.status_code != 200:
            err = resp.json().get("errors", [{}])[0].get("title", "Unknown error")
            raise RuntimeError(f"remove.bg error: {err}")

        return base64.b64encode(resp.content).decode("utf-8")


async def remove_background_from_bytes(image_bytes: bytes) -> bytes:
    """Удаляет фон из переданных байт изображения."""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": ("image.jpg", image_bytes, "image/jpeg")},
            data={"size": "auto", "type": "product", "format": "png"},
            headers={"X-Api-Key": config.REMOVE_BG_API_KEY},
        )
        resp.raise_for_status()
        return resp.content
