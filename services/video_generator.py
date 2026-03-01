import httpx
import asyncio
import jwt
import time
from config import config


def _get_kling_token() -> str:
    """Генерирует JWT-токен для Kling AI API."""
    payload = {
        "iss": config.KLING_API_KEY,
        "exp": int(time.time()) + 1800,
        "nbf": int(time.time()) - 5,
    }
    return jwt.encode(payload, config.KLING_API_SECRET, algorithm="HS256")


async def generate_fashion_video(
    image_url: str,
    prompt: str,
    duration: int = 5,
) -> str:
    """
    Генерирует короткое видео из изображения через Kling AI API (image2video).
    Returns URL готового видео.

    Docs: https://platform.klingai.com/docs
    """
    token = _get_kling_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "model_name": "kling-v1",
        "image": image_url,
        "prompt": prompt,
        "negative_prompt": "blurry, low quality, distorted, bad anatomy",
        "cfg_scale": 0.5,
        "mode": "std",
        "duration": str(duration),
        "aspect_ratio": "9:16",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.klingai.com/v1/videos/image2video",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"Kling AI error: {data.get('message')}")

        task_id = data["data"]["task_id"]

    async with httpx.AsyncClient(timeout=30) as client:
        for _ in range(60):
            await asyncio.sleep(10)
            fresh_token = _get_kling_token()
            status_resp = await client.get(
                f"https://api.klingai.com/v1/videos/image2video/{task_id}",
                headers={"Authorization": f"Bearer {fresh_token}"},
            )
            status_data = status_resp.json()
            task_status = status_data.get("data", {}).get("task_status")

            if task_status == "succeed":
                videos = status_data["data"]["task_result"]["videos"]
                if videos:
                    return videos[0]["url"]
                raise RuntimeError("Kling AI: пустой список видео")

            if task_status == "failed":
                raise RuntimeError(f"Kling AI task failed: {status_data}")

    raise TimeoutError("Kling AI: превышено время ожидания (600 сек)")
