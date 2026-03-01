from telegram import Bot
from config import config
from storage.redis_client import set_state, get_state, push_job
from bot.keyboards import approval_keyboard
from services.scraper import fetch_product_data
from services.bg_remover import remove_background
from services.prompt_generator import generate_model_prompt, generate_video_caption
from services.tryon import generate_virtual_tryon
from services.video_generator import generate_fashion_video
from services.video_assembler import assemble_final_video

bot = Bot(token=config.TELEGRAM_TOKEN)


async def process_job(job: dict):
    """Главный обработчик заданий из очереди Redis."""
    chat_id = job["chat_id"]
    step = job["step"]
    print(f"[pipeline] chat_id={chat_id}, step={step}")

    try:
        handlers = {
            "SCRAPING_PHOTO":   _step_scrape,
            "REMOVING_BG":      _step_remove_bg,
            "GENERATING_TRYON": _step_tryon,
            "GENERATING_VIDEO": _step_generate_video,
            "ASSEMBLING_VIDEO": _step_assemble,
        }
        handler = handlers.get(step)
        if handler:
            await handler(chat_id, job)
        else:
            raise ValueError(f"Unknown step: {step}")

    except Exception as exc:
        print(f"[pipeline] ERROR at {step}: {exc}")
        set_state(chat_id, "IDLE")
        await bot.send_message(
            chat_id,
            f"❌ Ошибка на шаге *{step}*:\n`{str(exc)[:300]}`\n\n"
            "Попробуйте снова — пришлите ссылку на товар.",
            parse_mode="Markdown",
        )


async def _step_scrape(chat_id: int, job: dict):
    product_data = await fetch_product_data(job["product_url"])
    new_job = {
        **job,
        "step": "REMOVING_BG",
        "image_url": product_data["image_url"],
        "product_name": product_data.get("product_name", ""),
        "product_price": product_data.get("product_price", ""),
    }
    set_state(chat_id, "REMOVING_BG", new_job)
    push_job(new_job)
    await bot.send_message(
        chat_id,
        f"✅ Фото получено!\n"
        f"📦 Товар: *{product_data.get('product_name', '')}*\n"
        f"🗑 Шаг 2/4: Удаляю фон...",
        parse_mode="Markdown",
    )


async def _step_remove_bg(chat_id: int, job: dict):
    clean_image_b64 = await remove_background(job["image_url"])
    prompt = generate_model_prompt(
        clothing_description=job.get("product_name", "fashion clothing"),
        product_name=job.get("product_name", ""),
    )
    state_data = {**job, "clean_image_b64": clean_image_b64, "prompt": prompt}
    set_state(chat_id, "WAITING_APPROVAL", state_data)
    await bot.send_message(
        chat_id,
        f"✅ Фон удалён!\n\n"
        f"🤖 *AI сгенерировал промпт для модели:*\n\n"
        f"_{prompt}_\n\n"
        "Подтвердить или отредактировать?",
        parse_mode="Markdown",
        reply_markup=approval_keyboard(),
    )


async def _step_tryon(chat_id: int, job: dict):
    tryon_image_url = await generate_virtual_tryon(
        clothing_image_b64=job["clean_image_b64"],
        prompt=job["prompt"],
    )
    new_job = {**job, "step": "GENERATING_VIDEO", "tryon_image_url": tryon_image_url}
    set_state(chat_id, "GENERATING_VIDEO", new_job)
    push_job(new_job)
    await bot.send_message(
        chat_id,
        "✅ Примерка готова!\n"
        "🎦 Шаг 4/4: Генерирую видео...\n"
        "⏱ ~2-5 минут",
    )


async def _step_generate_video(chat_id: int, job: dict):
    video_url = await generate_fashion_video(
        image_url=job["tryon_image_url"],
        prompt=job["prompt"],
        duration=5,
    )
    new_job = {**job, "step": "ASSEMBLING_VIDEO", "raw_video_url": video_url}
    set_state(chat_id, "ASSEMBLING_VIDEO", new_job)
    push_job(new_job)


async def _step_assemble(chat_id: int, job: dict):
    final_video_bytes = await assemble_final_video(
        video_url=job["raw_video_url"],
        product_name=job.get("product_name", ""),
        product_price=job.get("product_price", ""),
    )
    caption = generate_video_caption(
        product_name=job.get("product_name", ""),
        product_price=job.get("product_price", ""),
    )
    await bot.send_video(
        chat_id=chat_id,
        video=final_video_bytes,
        caption=f"🎉 *Ваш рекламный рилс готов!*\n\n{caption}",
        parse_mode="Markdown",
        width=1080,
        height=1920,
    )
    set_state(chat_id, "IDLE")
    await bot.send_message(
        chat_id,
        "✅ Готово! Пришлите новую ссылку для следующего видео.",
    )
