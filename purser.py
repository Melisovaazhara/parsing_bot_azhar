import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class ITProgerParser:
    def __init__(self):
        self.base_url = "https://itproger.com/news"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/91.0.4472.124 Safari/537.36'
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
            return []

    def _parse_article_container(self, container):
        """Парсит отдельный контейнер статьи"""
        article = {}

        # Заголовок
        title_elem = container.find(['h2', 'h3', 'h4', 'h1'])
        if not title_elem:
            title_elem = container.find('a', class_=lambda x: x and 'title' in x)
        article['title'] = title_elem.get_text().strip() if title_elem else "Без заголовка"

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
            article['description'] = first_p.get_text().strip()[:200] + "..." if first_p else "Описание недоступно"

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
                    'description': "Читайте полный текст статьи...",
                    'image_url': ""
                }
                articles.append(article)
            except Exception as e:
                logger.error(f"Ошибка альтернативного парсинга: {e}")
                continue

        return articles

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
                return text[:3000]  # Ограничиваем длину
            else:
                return "Полное содержимое статьи недоступно"

        except Exception as e:
            logger.error(f"Ошибка при получении полного контента: {e}")
            return "Ошибка при загрузке содержимого статьи"
