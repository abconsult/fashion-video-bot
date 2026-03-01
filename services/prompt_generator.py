from openai import OpenAI
from config import config

_client = OpenAI(
    base_url="https://ai.pro-talk.ru/v1",
    api_key=config.PROTALK_API_KEY,
)

SYSTEM_PROMPT_MODEL = """Ты — профессиональный fashion-стилист и режиссёр видео.
По описанию одежды создай промпт для AI-генерации fashion-видео с виртуальной моделью.

Требования:
- Язык: английский
- Длина: 40-60 слов
- Укажи: возраст/внешность модели, стиль съёмки, освещение, фон
- Фокус на демонстрации одежды
- Формат: одно описательное предложение

Отвечай ТОЛЬКО промптом, без пояснений."""

SYSTEM_PROMPT_CAPTION = """Создай короткую рекламную подпись для видео-рилс в Instagram.
Требования: 2-3 строки + 3-5 хэштегов. Язык: русский. Стиль: модный, живой."""


def generate_model_prompt(clothing_description: str, product_name: str = "") -> str:
    """
    Генерирует промпт для AI-видео через ProTalk API (OpenAI-compatible).
    """
    response = _client.chat.completions.create(
        model=config.PROTALK_MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_MODEL},
            {"role": "user", "content": f"Одежда: {product_name}\nОписание: {clothing_description}"},
        ],
        temperature=0.7,
        max_tokens=150,
        stream=False,
    )
    return response.choices[0].message.content.strip()


def generate_video_caption(product_name: str, product_price: str) -> str:
    """Генерирует подпись/капшн для финального видео."""
    response = _client.chat.completions.create(
        model=config.PROTALK_MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_CAPTION},
            {"role": "user", "content": f"Товар: {product_name}, цена: {product_price}"},
        ],
        temperature=0.8,
        max_tokens=100,
    )
    return response.choices[0].message.content.strip()
