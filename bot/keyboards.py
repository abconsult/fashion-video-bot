from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def model_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора модели перед генерацией примерки."""
    keyboard = [
        [
            InlineKeyboardButton("👱‍♀️ Блондинка", callback_data="model_1"),
            InlineKeyboardButton("👩🏻 Азиатка", callback_data="model_2"),
        ],
        [
            InlineKeyboardButton("👩🏾 Афроамериканка", callback_data="model_3"),
            InlineKeyboardButton("🎲 Случайная", callback_data="model_random")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def approval_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения промпта перед генерацией."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить и выбрать модель", callback_data="prompt_approve"),
        ],
        [
            InlineKeyboardButton("✏️ Редактировать промпт", callback_data="prompt_edit")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для отмены текущего действия."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Отмена", callback_data="action_cancel")]
    ])
