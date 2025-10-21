from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_article_keyboard(article_hash, page, is_last=False):
    buttons = [
        [
            InlineKeyboardButton("📖 Полный текст", callback_data=f"full_{article_hash}"),
            InlineKeyboardButton("🔗 Открыть статью", url=article['link'])
        ]
    ]

    if is_last:
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"prev_{page}"))
        nav_buttons.append(InlineKeyboardButton("➡️ Вперед", callback_data=f"next_{page}"))
        buttons.append(nav_buttons)

    return InlineKeyboardMarkup(buttons)

def get_navigation_keyboard(article_hash, page):
    buttons = [
        [
            InlineKeyboardButton("📖 Полный текст", callback_data=f"full_{article_hash}"),
            InlineKeyboardButton("🔗 Открыть статью", url=article['link'])
        ],
        [
            InlineKeyboardButton("⬅️ Назад", callback_data=f"prev_{page}"),
            InlineKeyboardButton("➡️ Вперед", callback_data=f"next_{page}")
        ]
    ]
    return InlineKeyboardMarkup(buttons)
