from telegram import Update
from telegram.ext import ContextTypes
from storage.redis_client import get_state, set_state, push_job
from bot.keyboards import cancel_keyboard, model_selection_keyboard

async def handle_prompt_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка кнопок под промптом (Одобрить / Редактировать).
    """
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    action = query.data  # prompt_approve или prompt_edit
    
    state_data = get_state(chat_id)
    if state_data.get("state") != "WAITING_APPROVAL":
        await query.edit_message_text("⚠️ Эта кнопка больше не актуальна. Пожалуйста, отправьте новую ссылку.")
        return

    if action == "prompt_edit":
        # Переводим в состояние ожидания текста
        set_state(chat_id, "WAITING_PROMPT_EDIT", state_data)
        await query.edit_message_text(
            f"Текущий промпт:\n`{state_data.get('prompt', '')}`\n\n"
            "Отправьте мне *новый текст промпта* в ответном сообщении.",
            parse_mode="Markdown",
            reply_markup=cancel_keyboard()
        )
    elif action == "prompt_approve":
        # Промпт подтвержден. Переходим к выбору модели.
        set_state(chat_id, "WAITING_MODEL_SELECTION", state_data)
        await query.edit_message_text(
            "✅ Промпт подтвержден!\n\n"
            "Теперь выберите виртуальную модель, на которую мы наденем одежду:",
            reply_markup=model_selection_keyboard()
        )

async def handle_prompt_edit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, state_data: dict):
    """
    Обработка текстового сообщения, когда пользователь редактирует промпт.
    """
    chat_id = update.effective_chat.id
    new_prompt = update.message.text.strip()
    
    # Обновляем промпт в задаче и переходим к выбору модели
    state_data["prompt"] = new_prompt
    set_state(chat_id, "WAITING_MODEL_SELECTION", state_data)
    
    await context.bot.send_message(
        chat_id=chat_id,
        text="✅ Новый промпт принят!\n\nТеперь выберите виртуальную модель:",
        reply_markup=model_selection_keyboard()
    )

async def handle_model_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка выбора модели (model_1, model_2, model_3, model_random).
    """
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    action = query.data
    
    state_data = get_state(chat_id)
    if state_data.get("state") != "WAITING_MODEL_SELECTION":
        await query.edit_message_text("⚠️ Эта кнопка больше не актуальна.")
        return
        
    # Извлекаем ID модели
    model_id = action.replace("model_", "")
    
    job = state_data
    job["model_id"] = model_id
    job["step"] = "GENERATING_TRYON"
    
    set_state(chat_id, "GENERATING_TRYON", job)
    push_job(job)
    
    await query.edit_message_text(
        "✅ Модель выбрана! Запускаю процесс виртуальной примерки..."
    )
