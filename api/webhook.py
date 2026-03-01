import os
import asyncio
from fastapi import FastAPI, Request, HTTPException
from telegram import Update, Bot
from config import config

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
        # Получаем данные из запроса
        data = await request.json()
        
        # Десериализуем объект Update
        update = Update.de_json(data, bot)
        
        # TODO: Заменить эхо-ответ на реальный диспетчер из bot.handlers
        # Пример того, как это будет выглядеть:
        # from bot.handlers.main_dispatcher import process_update
        # await process_update(update)
        
        # Временная заглушка-эхо для проверки работоспособности вебхука
        if update.message and update.message.text:
            await bot.send_message(
                chat_id=update.message.chat_id,
                text=f"Вебхук успешно принят! Вы написали: {update.message.text}"
            )
            
        return {"ok": True}
    except Exception as e:
        print(f"Webhook processing error: {e}")
        # Возвращаем 200/True в Telegram, чтобы он не зацикливал отправку сбойного апдейта
        return {"ok": True, "error": str(e)}

@app.get("/api/webhook")
async def webhook_health_check():
    """Проверка доступности эндпоинта для Vercel."""
    return {"status": "active", "message": "Telegram Webhook API is running"}
