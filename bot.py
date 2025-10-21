import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import html
import hashlib
import logging
from urllib.parse import urljoin

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = "8400111810:AAEm3p2S71750rYde1ydxwG6AfkYU0QLhfs"


class ITProgerParser:
    def __init__(self):
        self.base_url = "https://itproger.com/news"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_articles(self, page=1):
        """Парсит статьи с указанной страницы"""
        try:
            if page == 1:
                url = self.base_url
            else:
                url = f"{self.base_url}/page-{page}"

            logger.info(f"Парсинг страницы: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []

            # Поиск контейнеров со статьями
            article_containers = soup.find_all('article', class_=lambda x: x and 'article' in x)

            if not article_containers:
                # Альтернативный поиск
                article_containers = soup.find_all('div', class_=lambda x: x and ('article' in x or 'news' in x))

            for container in article_containers:
                try:
                    article_data = self._parse_article_container(container)
                    if article_data and article_data['title']:
                        articles.append(article_data)
                except Exception as e:
                    logger.error(f"Ошибка парсинга контейнера статьи: {e}")
                    continue

            # Если на первой странице нет статей, пробуем альтернативный метод
            if not articles and page == 1:
                articles = self._alternative_parse(soup)

            logger.info(f"Найдено статей: {len(articles)}")
            return articles[:10]  # Ограничиваем количество статей

        except Exception as e:
            logger.error(f"Ошибка при парсинге страницы {page}: {e}")
            return self._get_demo_articles(page)

    def _parse_article_container(self, container):
        """Парсит отдельный контейнер статьи"""
        article = {}

        # Заголовок
        title_elem = container.find(['h2', 'h3', 'h4', 'h1'])
        if not title_elem:
            title_elem = container.find('a', class_=lambda x: x and 'title' in x)
        article['title'] = title_elem.get_text().strip() if title_elem else "IT News Article"

        # Ссылка
        link_elem = container.find('a', href=True)
        if link_elem:
            article['link'] = urljoin(self.base_url, link_elem['href'])
        else:
            article['link'] = self.base_url

        # Описание
        desc_elem = container.find(['p', 'div'], class_=lambda x: x and ('desc' in x or 'content' in x or 'text' in x))
        if desc_elem:
            article['description'] = desc_elem.get_text().strip()[:200] + "..."
        else:
            # Берем первый параграф
            first_p = container.find('p')
            article['description'] = first_p.get_text().strip()[
                                     :200] + "..." if first_p else "IT news and programming tutorials..."

        # Изображение
        img_elem = container.find('img', src=True)
        if img_elem:
            article['image_url'] = urljoin(self.base_url, img_elem['src'])
        else:
            article['image_url'] = ""

        return article

    def _alternative_parse(self, soup):
        """Альтернативный метод парсинга"""
        articles = []

        # Поиск по ссылкам с новостями
        news_links = soup.find_all('a', href=lambda x: x and '/news/' in x, class_=False)

        for link in news_links[:10]:
            try:
                article = {
                    'title': link.get_text().strip() or "Новость ITProger",
                    'link': urljoin(self.base_url, link['href']),
                    'description': "Читайте полный текст статьи на сайте...",
                    'image_url': ""
                }
                articles.append(article)
            except Exception as e:
                logger.error(f"Ошибка альтернативного парсинга: {e}")
                continue

        return articles

    def _get_demo_articles(self, page):
        """Демо статьи если парсинг не удался"""
        return [
            {
                'title': f'IT News Page {page} - Article 1',
                'description': 'Latest programming news and updates from the IT world. Learn about new technologies '
                               'and frameworks.',
                'link': 'https://itproger.com/news',
                'image_url': ''
            },
            {
                'title': f'Programming Tutorials - Page {page}',
                'description': 'Learn new programming languages and frameworks with step-by-step tutorials '
                               'and examples.',
                'link': 'https://itproger.com/news',
                'image_url': ''
            },
            {
                'title': f'Tech Updates - Page {page}',
                'description': 'Stay updated with the latest technology trends and developments in the '
                               'programming world.',
                'link': 'https://itproger.com/news',
                'image_url': ''
            }
        ]

    def get_full_content(self, article_url):
        """Получает полное содержимое статьи"""
        try:
            response = self.session.get(article_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Ищем основной контент статьи
            content_div = soup.find('div', class_=lambda x: x and ('content' in x or 'article' in x or 'post' in x))

            if content_div:
                # Удаляем ненужные элементы (скрипты, стили)
                for elem in content_div.find_all(['script', 'style', 'nav', 'header', 'footer']):
                    elem.decompose()

                # Получаем текст
                text = content_div.get_text(separator='\n', strip=True)
                if text:
                    return text[:3000]  # Ограничиваем длину
                else:
                    return "⏳ Полное содержимое статьи будет доступно в ближайшее время. Используйте кнопку '🔗" \
                           " Открыть статью' для чтения на сайте."
            else:
                return "⏳ Полное содержимое статьи будет доступно в ближайшее время. Используйте кнопку '🔗 " \
                       "Открыть статью' для чтения на сайте."

        except Exception as e:
            logger.error(f"Ошибка при получении полного контента: {e}")
            return "⏳ Полное содержимое статьи будет доступно в ближайшее время. Используйте кнопку '🔗" \
                   " Открыть статью' для чтения на сайте."


class ITProgerBot:
    def __init__(self):
        self.parser = ITProgerParser()
        self.user_data = {}
        self.article_cache = {}

    def _get_short_hash(self, url):
        """Создает короткий хэш для URL"""
        return hashlib.md5(url.encode()).hexdigest()[:10]

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        welcome_text = f"""
👋 Привет, {user.first_name}!

🤖 Я бот для чтения IT статей с itproger.com/news

📚 Доступные команды:
/news - Последние статьи
/next - Следующая страница
/prev - Предыдущая страница

🎛️ Используй кнопки ниже для навигации!
        """

        # Reply клавиатура
        reply_keyboard = [
            ["📰 Последние новости"],
            ["➡️ Следующая страница", "⬅️ Предыдущая страница"],
            ["ℹ️ Помощь"]
        ]

        await update.message.reply_text(
            welcome_text,
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                resize_keyboard=True,
                input_field_placeholder="Выберите действие..."
            )
        )

    async def show_news(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает последние новости"""
        user_id = update.effective_user.id
        self.user_data[user_id] = {'current_page': 1}

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action='typing'
        )
        await self._send_articles(update, context, page=1)

    async def next_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Следующая страница"""
        user_id = update.effective_user.id

        if user_id not in self.user_data:
            self.user_data[user_id] = {'current_page': 1}

        current_page = self.user_data[user_id]['current_page']
        next_page = current_page + 1

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action='typing'
        )
        await self._send_articles(update, context, page=next_page)

    async def prev_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Предыдущая страница"""
        user_id = update.effective_user.id

        if user_id not in self.user_data:
            self.user_data[user_id] = {'current_page': 1}

        current_page = self.user_data[user_id]['current_page']
        prev_page = max(1, current_page - 1)

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action='typing'
        )
        await self._send_articles(update, context, page=prev_page)

    async def _send_articles(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
        """Отправляет статьи указанной страницы"""
        user_id = update.effective_user.id
        self.user_data[user_id] = {'current_page': page}

        # Получаем статьи
        articles = self.parser.get_articles(page)

        if not articles:
            await update.message.reply_text(
                "❌ Не удалось загрузить статьи. Попробуйте позже."
            )
            return

        # Сохраняем статьи в кэш
        cache_key = f"{user_id}_{page}"
        self.article_cache[cache_key] = articles

        # Инлайн клавиатура для навигации
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"prev_{page}"))
        nav_buttons.append(InlineKeyboardButton("➡️ Вперед", callback_data=f"next_{page}"))

        navigation = [nav_buttons] if nav_buttons else []

        # Отправляем каждую статью отдельным сообщением
        for i, article in enumerate(articles, 1):
            message_text = self._format_article_message(article, i, page)

            # Создаем короткий идентификатор для статьи
            article_hash = self._get_short_hash(article['link'])

            # Кнопки для статьи
            article_buttons = [
                [
                    InlineKeyboardButton("📖 Полный текст", callback_data=f"full_{article_hash}"),
                    InlineKeyboardButton("🔗 Открыть статью", url=article['link'])
                ]
            ]

            # Сохраняем ссылку по хэшу
            self.article_cache[article_hash] = article['link']

            # Добавляем навигацию к последней статье
            if i == len(articles):
                article_buttons.extend(navigation)

            reply_markup = InlineKeyboardMarkup(article_buttons)

            try:
                if article.get('image_url') and article['image_url'].startswith('http'):
                    await update.message.reply_photo(
                        photo=article['image_url'],
                        caption=message_text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                else:
                    await update.message.reply_text(
                        message_text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
            except Exception as e:
                # Если не удалось отправить с фото, отправляем только текст
                logger.error(f"Ошибка отправки фото: {e} для URL: {article.get('image_url', 'Нет URL')}")
                await update.message.reply_text(
                    message_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )

    def _format_article_message(self, article, index, page):
        """Форматирует сообщение со статьей"""
        title = html.escape(article['title'])
        description = html.escape(article['description'])

        return f"""
📰 <b>{title}</b>

📝 {description}

📄 Страница: {page} | Статья: {index}
        """

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на инлайн кнопки"""
        query = update.callback_query
        await query.answer()

        data = query.data
        user_id = query.from_user.id

        if data.startswith('full_'):
            # Кнопка "Полный текст"
            article_hash = data[5:]
            article_url = self.article_cache.get(article_hash)

            if article_url:
                full_content = self.parser.get_full_content(article_url)

                if full_content and full_content != "Полное содержимое статьи недоступно":
                    # Экранируем HTML символы
                    content = html.escape(full_content)
                    # Ограничиваем длину сообщения
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
            # Следующая страница
            current_page = int(data[5:])
            next_page = current_page + 1
            await self._handle_navigation(query, context, next_page)

        elif data.startswith('prev_'):
            # Предыдущая страница
            current_page = int(data[5:])
            prev_page = max(1, current_page - 1)
            await self._handle_navigation(query, context, prev_page)

    async def _handle_navigation(self, query, context: ContextTypes.DEFAULT_TYPE, page: int):
        """Обрабатывает навигацию по страницам"""
        user_id = query.from_user.id
        self.user_data[user_id] = {'current_page': page}

        articles = self.parser.get_articles(page)
        if not articles:
            await query.message.reply_text("❌ Не удалось загрузить статьи для этой страницы.")
            return

        # Удаляем старое сообщение
        await query.message.delete()

        # Отправляем новые статьи
        for i, article in enumerate(articles, 1):
            message_text = self._format_article_message(article, i, page)
            article_hash = self._get_short_hash(article['link'])

            # Кнопки для статьи
            nav_buttons = []
            if page > 1:
                nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"prev_{page}"))
            nav_buttons.append(InlineKeyboardButton("➡️ Вперед", callback_data=f"next_{page}"))

            article_buttons = [
                [
                    InlineKeyboardButton("📖 Полный текст", callback_data=f"full_{article_hash}"),
                    InlineKeyboardButton("🔗 Открыть статью", url=article['link'])
                ],
                nav_buttons
            ]

            self.article_cache[article_hash] = article['link']
            reply_markup = InlineKeyboardMarkup(article_buttons)

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


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
🤖 Доступные команды:
/start - Запуск бота и вывод приветственного сообщения.
/news - Отображение последних статей с первой страницы.
/next - Переход к следующей странице статей.
/prev - Переход к предыдущей странице статей.
/help - Вывод справки о командах бота.

🎛️ Используйте кнопки навигации для перемещения по страницам и просмотра полных текстов статей.
    """
    await update.message.reply_text(help_text)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    text = update.message.text

    # Получаем экземпляр бота из обработчиков
    bot = None
    for handler in context.application.handlers[0]:
        if hasattr(handler, 'callback') and hasattr(handler.callback, '__self__'):
            bot = handler.callback.__self__
            break

    if not bot:
        await update.message.reply_text("❌ Ошибка системы. Попробуйте позже.")
        return

    if text == "📰 Последние новости":
        await bot.show_news(update, context)
    elif text == "➡️ Следующая страница":
        await bot.next_page(update, context)
    elif text == "⬅️ Предыдущая страница":
        await bot.prev_page(update, context)
    elif text == "ℹ️ Помощь":
        await help_command(update, context)
    else:
        await update.message.reply_text("Я не понимаю эту команду. Используйте кнопки или команды из меню.")


async def post_init(application: Application):
    """Выполняется после инициализации приложения"""
    logger.info("Бот успешно запущен и готов к работе!")


def main():
    """Основная функция запуска бота"""
    bot = ITProgerBot()

    application = Application.builder() \
        .token(BOT_TOKEN) \
        .post_init(post_init) \
        .build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("news", bot.show_news))
    application.add_handler(CommandHandler("next", bot.next_page))
    application.add_handler(CommandHandler("prev", bot.prev_page))
    application.add_handler(CommandHandler("help", help_command))

    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Обработчик нажатий на кнопки
    application.add_handler(CallbackQueryHandler(bot.button_handler))

    # Запускаем бота
    logger.info("Запуск бота...")
    application.run_polling()


if __name__ == '__main__':
    main()
