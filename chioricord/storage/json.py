"""Функции для чтения и записи json файлов.

Используются когда нужно простое файловое хранилище данных.
Для более больших плагинов лучше использовать базы данных.

Author: Milinuri Nirvalen
"""

import json
from pathlib import Path

# Функции для работы с json
# =========================

def write_json(path: Path, content: dict) -> None:
    """Записывает данные в JSON фалй.

    Простая фунеция для записи некоторого словаря в файл.
    Используется когда нужно осхранть простые данные в файл.
    Если нужного файла не существует, он будет автоматически
    создан.

    :param path: Путь к файлу для записи данных.
    :type path: Path
    :param content: Словарь для записи в файл.
    :type content: dict
    """
    if not path.exists():
        path.parents[0].mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        json.dump(content, f, ensure_ascii=True, indent=4)

def load_json(path: Path, data: dict | None = None) -> dict | None:
    """Загружает данные из файла.

    Используется когда просто нужно загрузить некоторые
    данные из JSON файла в словарь.
    Обратите вниманеи что данные никак не валидируются.
    Также вы можете передать словарь по умолчанию.
    Если нужного файла не существует и вы указали данные
    по умолчанию, то по указанному пути сразу будет создан
    файл с данными по умолчанию.

    :param path: Путь к файлу для запгрузки данных.
    :type path: Path
    :param data: Данные файла по умолчанию или None.
    :type data: dict, optional
    :return: Загруженный словарь из файла или None
    :rtype: dict, optional
    """
    if not path.exists() and data is not None:
        write_json(path, data)

    with open(path) as f:
        return json.load(f)
