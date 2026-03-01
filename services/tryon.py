import httpx
import random
from typing import Optional, Dict
from config import config

# Пул базовых фотографий моделей с описаниями
MODELS_POOL = {
    "1": {
        "name": "Европейский типаж, блондинка",
        "url": "https://fashn.ai/examples/model_standing_neutral.jpg"
    },
    "2": {
        "name": "Азиатский типаж, брюнетка",
        "url": "https://fashn.ai/examples/model_2_neutral.jpg"
    },
    "3": {
        "name": "Афроамериканский типаж",
        "url": "https://fashn.ai/examples/model_3_pose.jpg"
    }
}

def get_random_model_url() -> str:
    """Выбирает случайную модель из пула."""
    model_key = random.choice(list(MODELS_POOL.keys()))
    return MODELS_POOL[model_key]["url"]

def get_model_url(model_id: str) -> str:
    """Возвращает URL модели по ID, или дефолтную, если ID нет."""
    if model_id in MODELS_POOL:
        return MODELS_POOL[model_id]["url"]
    return get_random_model_url()

async def start_virtual_tryon(
    clothing_image_b64: str,
    prompt: str,
    category: str = "tops",
    model_image_url: Optional[str] = None
) -> str:
    """
    Отправляет задачу на генерацию примерки в Fashn.ai.
    """
    headers = {
        "Authorization": f"Bearer {config.FASHN_API_KEY}",
        "Content-Type": "application/json",
    }
    
    # Если URL модели не передан, берем случайную из пула
    selected_model = model_image_url if model_image_url else get_random_model_url()
    
    payload = {
        "model_image": selected_model,
        "garment_image": f"data:image/png;base64,{clothing_image_b64}",
        "category": category, # Используем динамическую категорию (tops, bottoms, one-pieces)
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
