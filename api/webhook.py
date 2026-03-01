from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from bot.handlers import process_update
from telegram import Update
from config import config
from storage.redis_client import get_state, set_state, push_job

app = FastAPI()

@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    """Эндпоинт для приема апдейтов от Telegram."""
    try:
        data = await request.json()
        update = Update.de_json(data, None)
        await process_update(update)
        return {"ok": True}
    except Exception as e:
        print(f"Error handling update: {e}")
        return {"ok": False, "error": str(e)}

@app.post("/api/kling_callback")
async def kling_callback(request: Request, background_tasks: BackgroundTasks):
    """
    Эндпоинт для приема webhook-коллбэков от ProTalk (Kling).
    Ожидает query параметры: token (для проверки) и chat_id (для идентификации юзера).
    """
    query_params = request.query_params
    token = query_params.get("token")
    chat_id_str = query_params.get("chat_id")

    if token != config.CRON_SECRET:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    if not chat_id_str:
        raise HTTPException(status_code=400, detail="Missing chat_id")
        
    chat_id = int(chat_id_str)
    
    try:
        # Читаем payload от ProTalk
        data = await request.json()
        print(f"[Webhook Kling] Received callback for chat {chat_id}: {data}")
        
        # ProTalk/Kling возвращает URL готового видео. Формат нужно будет уточнить на практике,
        # но обычно это data.get("video_url") или data.get("url") или data.get("output")[0]
        # Предположим стандартный формат ответа ProTalk/KIE:
        video_url = data.get("video_url") or data.get("url")
        
        if not video_url:
            # Возможно это уведомление об ошибке
            error_msg = data.get("error", "Unknown error in Kling callback")
            print(f"[Webhook Kling] Error in callback: {error_msg}")
            
            # Сбрасываем статус
            set_state(chat_id, "IDLE")
            
            # Отправляем сообщение юзеру (в фоне)
            from bot.handlers import application # Осторожный импорт, чтобы избежать циклов
            bot = application.bot
            background_tasks.add_task(
                bot.send_message,
                chat_id=chat_id,
                text=f"❌ Ошибка генерации видео: {error_msg}"
            )
            return {"status": "error processed"}

        # Достаем текущую задачу из Redis
        job = get_state(chat_id)
        if not job or job.get("step") != "WAITING_VIDEO_WEBHOOK":
            print(f"[Webhook Kling] Ignore callback: user {chat_id} is not waiting for video.")
            return {"status": "ignored"}
            
        # Обновляем задачу и пушим её в очередь для финальной сборки (Cloudinary)
        new_job = {
            **job,
            "step": "ASSEMBLING_VIDEO",
            "raw_video_url": video_url
        }
        set_state(chat_id, "ASSEMBLING_VIDEO", new_job)
        
        # Вместо того чтобы ждать крона, мы можем пушнуть задачу в редис,
        # чтобы крон подхватил ее на следующей минуте (безопасно для Vercel таймаутов).
        push_job(new_job)
        
        return {"status": "success", "queued": True}

    except Exception as e:
        print(f"[Webhook Kling] Fatal error handling callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))
