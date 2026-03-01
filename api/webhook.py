import os
import asyncio
from fastapi import FastAPI, Request, HTTPException
from telegram import Update, Bot
from config import config

# Импортируем наш настоящий диспетчер
from bot.handlers import process_update

app = FastAPI()

# Инициализируем бота
bot = Bot(token=config.TELEGRAM_TOKEN)

@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    """
    Основной обработчик вебхуков от Telegram.
    Принимает обновления и передает их в логику бота.
    """
    if not config.TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN is not configured")
        return {"ok": False, "error": "Token missing"}

    try:
        data = await request.json()
        update = Update.de_json(data, bot)
        
        # Передаем Update в реальную логику обработчиков (handlers)
        await process_update(update)
            
        return {"ok": True}
    except Exception as e:
        print(f"Webhook processing error: {e}")
        # Возвращаем 200/True в Telegram, чтобы он не зацикливал отправку сбойного апдейта
        return {"ok": True, "error": str(e)}

@app.get("/api/webhook")
async def webhook_health_check():
    """Проверка доступности эндпоинта для Vercel."""
    return {"status": "active", "message": "Telegram Webhook API is running"}
