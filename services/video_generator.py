import httpx
import json
import urllib.parse
from typing import Dict, Optional
from config import config

async def start_fashion_video(
    image_url: str,
    prompt: str,
    chat_id: int,
    duration: int = 5,
) -> str:
    """
    Отправляет задачу на генерацию видео через функцию ProTalk №585 (Kling 2.6).
    Передает callBackUrl для получения результата на Vercel.
    Возвращает статус "ok" если запрос принят.
    """
    # Собираем URL для вебхука с токеном безопасности и ID чата
    base_url = config.VERCEL_URL.rstrip('/')
    if not base_url.startswith("http"):
        base_url = f"https://{base_url}"
        
    callback_url = f"{base_url}/api/kling_callback?token={config.CRON_SECRET}&chat_id={chat_id}"

    # Параметры для функции 585
    params = {
        "prompt": prompt,
        "image_urls": image_url,
        "duration": str(duration),
        "sound": False,
        "taskId_only": True,
        "callBackUrl": callback_url
    }

    # Формируем сообщение: номер функции + JSON с новой строки
    message_text = f"585\n{json.dumps(params, ensure_ascii=False)}"

    payload = {
        "bot_id": config.PROTALK_BOT_ID,
        "bot_token": config.PROTALK_BOT_TOKEN,
        "bot_chat_id": f"kling_{chat_id}",
        "message": message_text
    }

    async with httpx.AsyncClient(timeout=30) as client:
        # Используем асинхронную отправку (не ждем генерации)
        resp = await client.post(
            "https://eu1.api.pro-talk.ru/api/v1.0/send_message_async",
            json=payload
        )
        resp.raise_for_status()
        
        # На данном этапе задача отправлена в ProTalk. Мы не можем моментально получить taskId
        # Поэтому просто возвращаем успех. Пайплайн остановится и будет ждать webhook (callback).
        return "async_task_started"


async def check_video_status(task_id: str) -> Dict[str, Optional[str]]:
    """
    Оставлено для обратной совместимости или ручного пуллинга,
    но в новой архитектуре результат придет через Webhook (callback).
    """
    # Если мы перешли на callback, этот метод нам больше не нужен для активного поллинга Kling.
    return {"status": "processing"}
