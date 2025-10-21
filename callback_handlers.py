from telegram import Update
from telegram.ext import ContextTypes
from bot.keyboards.inline import get_navigation_keyboard
import html
import logging

logger = logging.getLogger(__name__)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id
    bot = context.bot_data['bot']

    if data.startswith('full_'):
        article_hash = data[5:]
        article_url = bot.article_cache.get(article_hash)

        if article_url:
            full_content = bot.parser.get_full_content(article_url)

            if full_content and full_content != "Полное содержимое статьи недоступно":
                content = html.escape(full_content)
                if len(content) > 3000:
                    content = content[:3000] + "...\n\n📖 <i>Читайте полную версию на сайте</i>"
                message = f"📖 <b>Полное содержимое:</b>\n\n{content}"
            else:
                message = "⏳ <b>Скоро!</b>\n\nПолное содержимое статьи будет доступно в ближайшее время."

            try:
                await query.message.reply_text(message, parse_mode='HTML')
            except Exception as e:
                logger.error(f"Ошибка отправки полного текста: {e}")
        else:
            await query.message.reply_text("❌ Статья не найдена")

    elif data.startswith('next_'):
        current_page = int(data[5:])
        next_page = current_page + 1
        await _handle_navigation(query, context, next_page)

    elif data.startswith('prev_'):
        current_page = int(data[5:])
        prev_page = max(1, current_page - 1)
        await _handle_navigation(query, context, prev_page)

async def _handle_navigation(query, context: ContextTypes.DEFAULT_TYPE, page: int):
    bot = context.bot_data['bot']
    user_id = query.from_user.id
    bot.user_data[user_id] = {'current_page': page}

    articles = bot.parser.get_articles(page)
    if not articles:
        await query.message.reply_text("❌ Не удалось загрузить статьи для этой страницы.")
        return

    await query.message.delete()

    for i, article in enumerate(articles, 1):
        message_text = _format_article_message(article, i, page)
        article_hash = bot._get_short_hash(article['link'])
        bot.article_cache[article_hash] = article['link']

        reply_markup = get_navigation_keyboard(article_hash, article['link'], page)

        try:
            if article.get('image_url') and article['image_url'].startswith('http'):
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=article['image_url'],
                    caption=message_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=message_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.error(f"Ошибка отправки статьи: {e}")
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=message_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

def _format_article_message(article, index, page):
    title = html.escape(article['title'])
    description = html.escape(article['description'])

    return f"""
📰 <b>{title}</b>

📝 {description}

📄 Страница: {page} | Статья: {index}
    """
