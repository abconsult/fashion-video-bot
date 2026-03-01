import httpx
import asyncio
from config import config

# Дефолтное изображение модели (замените на свой URL или базу моделей)
DEFAULT_MODEL_IMAGE = "https://fashn.ai/examples/model_standing_neutral.jpg"


async def generate_virtual_tryon(
    clothing_image_b64: str,
    prompt: str,
    category: str = "tops",
) -> str:
    """
    Генерирует виртуальную примерку одежды на AI-модели через Fashn.ai API.
    Returns URL готового изображения примерки.

    Docs: https://fashn.ai/docs
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

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.fashn.ai/v1/run",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        prediction_id = resp.json().get("id")

        if not prediction_id:
            raise RuntimeError("Fashn.ai: не получен ID задачи")

        for _ in range(30):
            await asyncio.sleep(5)
            status_resp = await client.get(
                f"https://api.fashn.ai/v1/status/{prediction_id}",
                headers=headers,
            )
            status_data = status_resp.json()
            status = status_data.get("status")

            if status == "completed":
                output = status_data.get("output", [])
                if output:
                    return output[0]
                raise RuntimeError("Fashn.ai: пустой output")

            if status in ("failed", "cancelled"):
                raise RuntimeError(f"Fashn.ai failed: {status_data.get('error')}")

    raise TimeoutError("Fashn.ai: превышено время ожидания (150 сек)")
