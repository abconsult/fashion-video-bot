import httpx
import jwt
import time
from typing import Dict, Optional
from config import config


def _get_kling_token() -> str:
    """Генерирует JWT-токен для Kling AI API."""
    payload = {
        "iss": config.KLING_API_KEY,
        "exp": int(time.time()) + 1800,
        "nbf": int(time.time()) - 5,
    }
    return jwt.encode(payload, config.KLING_API_SECRET, algorithm="HS256")


async def start_fashion_video(
    image_url: str,
    prompt: str,
    duration: int = 5,
) -> str:
    """
    Отправляет задачу на генерацию видео в Kling AI API.
    Возвращает task_id задачи, не дожидаясь выполнения.
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

        return data["data"]["task_id"]


async def check_video_status(task_id: str) -> Dict[str, Optional[str]]:
    """
    Проверяет статус задачи в Kling AI.
    Возвращает {"status": "processing"|"completed"|"failed", "url": "...", "error": "..."}
    """
    token = _get_kling_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"https://api.klingai.com/v1/videos/image2video/{task_id}",
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        
        if data.get("code") != 0:
             return {"status": "failed", "error": data.get("message")}
             
        task_data = data.get("data", {})
        task_status = task_data.get("task_status")

        if task_status == "succeed":
            videos = task_data.get("task_result", {}).get("videos", [])
            if videos:
                return {"status": "completed", "url": videos[0]["url"]}
            return {"status": "failed", "error": "Empty videos array"}

        if task_status == "failed":
            return {"status": "failed", "error": str(data)}

        return {"status": "processing"}
