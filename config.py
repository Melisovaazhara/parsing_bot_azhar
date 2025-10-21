from dataclasses import dataclass


@dataclass
class BotConfig:
    TOKEN: str = "8400111810:AAEm3p2S71750rYde1ydxwG6AfkYU0QLhfs"
    PARSE_MODE: str = "Markdown"
    REQUEST_TIMEOUT: int = 10


@dataclass
class ParserConfig:
    BASE_URL: str = "https://itproger.com/news"
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)" \
                      " Chrome/120.0.0.0 Safari/537.36"
    MAX_ARTICLES: int = 8
    MAX_CONTENT_LENGTH: int = 2500