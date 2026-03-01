from openai import AsyncOpenAI
import json
from config import config

_client = AsyncOpenAI(
    base_url="https://ai.pro-talk.ru/v1",
    api_key=config.PROTALK_API_KEY,
)

SYSTEM_PROMPT_MODEL = """Ты — профессиональный fashion-стилист и классификатор одежды.
Твоя задача — проанализировать название и описание товара и вернуть JSON-объект.

В JSON должно быть два поля:
1. "category": строго одно из значений: "tops" (верх: футболки, куртки, худи), "bottoms" (низ: штаны, юбки, шорты), "one-pieces" (цельные вещи: платья, комбинезоны).
2. "prompt": промпт для AI-генерации fashion-видео с виртуальной моделью (английский язык, 40-60 слов, фокус на внешности модели, освещении и фоне).

Отвечай СТРОГО в формате валидного JSON без маркдауна и лишних символов."""

SYSTEM_PROMPT_CAPTION = """Создай короткую рекламную подпись для видео-рилс в Instagram.
Требования: 2-3 строки + 3-5 хэштегов. Язык: русский. Стиль: модный, живой."""


async def generate_model_prompt_and_category(clothing_description: str, product_name: str = "") -> dict:
    """
    Генерирует промпт для AI-видео и определяет категорию (tops/bottoms/one-pieces).
    Возвращает dict: {"category": "tops", "prompt": "..."}
    """
    try:
        response = await _client.chat.completions.create(
            model=config.PROTALK_MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_MODEL},
                {"role": "user", "content": f"Одежда: {product_name}\nОписание: {clothing_description}"},
            ],
            temperature=0.3, # Снижаем температуру для более предсказуемого JSON
            max_tokens=200,
        )
        content = response.choices[0].message.content.strip()
        
        # Очистка от возможных markdown-тегов ```json ... ```
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            if content.endswith("```"):
                content = content.rsplit("\n", 1)[0]
                
        data = json.loads(content)
        
        # Валидация категории
        if data.get("category") not in ["tops", "bottoms", "one-pieces"]:
            data["category"] = "tops" # фоллбэк
            
        return {
            "category": data.get("category", "tops"),
            "prompt": data.get("prompt", "Beautiful fashion model posing in natural light")
        }
    except Exception as e:
        print(f"Error parsing AI prompt response: {e}")
        return {"category": "tops", "prompt": "Beautiful fashion model wearing the product, photorealistic, 4k"}


async def generate_video_caption(product_name: str, product_price: str) -> str:
    """Генерирует подпись/капшн для финального видео."""
    response = await _client.chat.completions.create(
        model=config.PROTALK_MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_CAPTION},
            {"role": "user", "content": f"Товар: {product_name}, цена: {product_price}"},
        ],
        temperature=0.8,
        max_tokens=100,
    )
    return response.choices[0].message.content.strip()
