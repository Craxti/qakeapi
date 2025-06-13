import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class MediaType:
    """Класс для работы с MIME-типами"""

    type: str
    subtype: str
    parameters: Dict[str, str]
    q: float = 1.0

    @classmethod
    def parse(cls, media_type_str: str) -> "MediaType":
        """Разбор строки MIME-типа"""
        # Разделяем тип и параметры
        parts = media_type_str.split(";")
        type_part = parts[0].strip()

        # Разделяем основной тип и подтип
        if "/" in type_part:
            type_, subtype = type_part.split("/", 1)
        else:
            type_, subtype = type_part, "*"

        # Разбираем параметры
        parameters = {}
        q = 1.0
        for part in parts[1:]:
            if "=" not in part:
                continue
            key, value = part.strip().split("=", 1)
            key = key.strip()
            value = value.strip().strip('"')
            if key == "q":
                q = float(value)
            else:
                parameters[key] = value

        return cls(type_, subtype, parameters, q)

    def matches(self, other: "MediaType") -> bool:
        """Проверить, соответствует ли тип другому типу"""
        # Проверяем основной тип
        if self.type != "*" and other.type != "*" and self.type != other.type:
            return False

        # Проверяем подтип
        if (
            self.subtype != "*"
            and other.subtype != "*"
            and self.subtype != other.subtype
        ):
            return False

        # Проверяем параметры (кроме q)
        for key, value in self.parameters.items():
            if key == "q":
                continue
            if key not in other.parameters or other.parameters[key] != value:
                return False

        return True

    def __str__(self) -> str:
        """Преобразование в строку"""
        result = f"{self.type}/{self.subtype}"
        for key, value in self.parameters.items():
            result += f'; {key}="{value}"'
        if self.q != 1.0:
            result += f"; q={self.q}"
        return result


class ContentNegotiator:
    """Класс для согласования содержимого"""

    def __init__(self):
        self.available_types: List[MediaType] = []
        self.available_languages: List[str] = []
        self.available_encodings: List[str] = []

    def add_type(self, media_type: str) -> None:
        """Добавить поддерживаемый тип содержимого"""
        self.available_types.append(MediaType.parse(media_type))

    def add_language(self, language: str) -> None:
        """Добавить поддерживаемый язык"""
        self.available_languages.append(language)

    def add_encoding(self, encoding: str) -> None:
        """Добавить поддерживаемую кодировку"""
        self.available_encodings.append(encoding)

    def negotiate_type(self, accept_header: str) -> Optional[MediaType]:
        """Согласовать тип содержимого"""
        if not accept_header:
            return self.available_types[0] if self.available_types else None

        # Разбираем заголовок Accept
        accepted_types = []
        for type_str in accept_header.split(","):
            try:
                media_type = MediaType.parse(type_str.strip())
                accepted_types.append(media_type)
            except ValueError:
                continue

        # Сортируем по q-фактору
        accepted_types.sort(key=lambda t: t.q, reverse=True)

        # Ищем первый подходящий тип
        for accepted in accepted_types:
            for available in self.available_types:
                if accepted.matches(available):
                    return available

        return None

    def negotiate_language(self, accept_language: str) -> Optional[str]:
        """Согласовать язык"""
        if not accept_language or not self.available_languages:
            return self.available_languages[0] if self.available_languages else None

        # Разбираем заголовок Accept-Language
        accepted_languages = []
        for lang_str in accept_language.split(","):
            parts = lang_str.strip().split(";")
            lang = parts[0].strip()
            q = 1.0
            if len(parts) > 1:
                q_str = parts[1].strip()
                if q_str.startswith("q="):
                    try:
                        q = float(q_str[2:])
                    except ValueError:
                        continue
            accepted_languages.append((lang, q))

        # Сортируем по q-фактору
        accepted_languages.sort(key=lambda l: l[1], reverse=True)

        # Ищем первый подходящий язык
        for lang, _ in accepted_languages:
            if lang == "*":
                return self.available_languages[0]
            if lang in self.available_languages:
                return lang
            # Проверяем соответствие по основному языку (en-US -> en)
            base_lang = lang.split("-")[0]
            for available in self.available_languages:
                if available.startswith(base_lang):
                    return available

        return None

    def negotiate_encoding(self, accept_encoding: str) -> Optional[str]:
        """Согласовать кодировку"""
        if not accept_encoding or not self.available_encodings:
            return self.available_encodings[0] if self.available_encodings else None

        # Разбираем заголовок Accept-Encoding
        accepted_encodings = []
        for enc_str in accept_encoding.split(","):
            parts = enc_str.strip().split(";")
            enc = parts[0].strip()
            q = 1.0
            if len(parts) > 1:
                q_str = parts[1].strip()
                if q_str.startswith("q="):
                    try:
                        q = float(q_str[2:])
                    except ValueError:
                        continue
            accepted_encodings.append((enc, q))

        # Сортируем по q-фактору
        accepted_encodings.sort(key=lambda e: e[1], reverse=True)

        # Ищем первую подходящую кодировку
        for enc, q in accepted_encodings:
            if q == 0:  # Кодировка явно запрещена
                continue
            if enc == "*":
                return self.available_encodings[0]
            if enc in self.available_encodings:
                return enc

        return None
