import httpx
from typing import Optional, Dict
from config import config

DEFAULT_MODEL_IMAGE = "https://fashn.ai/examples/model_standing_neutral.jpg"

async def start_virtual_tryon(
    clothing_image_b64: str,
    prompt: str,
    category: str = "tops",
) -> str:
    """
    Отправляет задачу на генерацию примерки в Fashn.ai.
    Возвращает prediction_id задачи, не дожидаясь выполнения.
    """
    headers = {
        "Authorization": f"Bearer {config.FASHN_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model_image": DEFAULT_MODEL_IMAGE,
        "garment_image": f"data:image/png;base64,{clothing_image_b64}",
        "category": category,
        "mode": "quality",
        "num_samples": 1,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.fashn.ai/v1/run",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        prediction_id = resp.json().get("id")

        if not prediction_id:
            raise RuntimeError("Fashn.ai: не получен ID задачи")
            
        return prediction_id


async def check_tryon_status(prediction_id: str) -> Dict[str, Optional[str]]:
    """
    Проверяет статус задачи в Fashn.ai.
    Возвращает {"status": "processing"|"completed"|"failed", "url": "...", "error": "..."}
    """
    headers = {
        "Authorization": f"Bearer {config.FASHN_API_KEY}",
        "Content-Type": "application/json",
    }
    
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"https://api.fashn.ai/v1/status/{prediction_id}",
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status")

        if status == "completed":
            output = data.get("output", [])
            if output:
                return {"status": "completed", "url": output[0]}
            return {"status": "failed", "error": "Empty output array"}

        if status in ("failed", "cancelled"):
            return {"status": "failed", "error": data.get("error", "Unknown error")}

        return {"status": "processing"}
