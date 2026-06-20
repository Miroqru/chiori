# Chiori

<p align="center">
  <img src="https://miroq.ru/assets/chio/ava.png" width=256>
</p>

<p align="center">
  <a href="https://github.com/astral-sh/ruff"><img alt="Ruff" src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json"></a>
  <img alt="Last Commit" src="https://img.shields.io/gitea/last-commit/chi/core?gitea_url=https%3A%2F%2Fgit.miroq.ru&style=flat&labelColor=%23805959&color=%23F68121">
  <img alt="Version" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fgit.miroq.ru%2Fchio%2Fcore%2Fraw%2Fbranch%2Fmain%2Fpyproject.toml&query=project.version&prefix=v&style=flat&label=Chiori&labelColor=%23B38B74&color=%232185A6">
  <img alt="LICENSE" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fgit.miroq.ru%2Fchio%2Fcore%2Fraw%2Fbranch%2Fmain%2Fpyproject.toml&query=project.license&style=flat&label=License&labelColor=%23B38B74&color=%2317B34B">
  <img alt="Discord" src="https://img.shields.io/discord/1282356859595919463?style=flat&label=Salor%3B%20land&labelColor=%23B38B74&color=%2373FFAD">
  <img alt="Docs" src="https://img.shields.io/badge/Miroq-docs?style=flat&label=Docs&labelColor=%23805959&color=%23B32D8A&link=https%3A%2F%2Fmiroq.ru%2Fchio%2F">
  <img alt="Python" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fgit.miroq.ru%2Fchio%2Fcore%2Fraw%2Fbranch%2Fmain%2Fpyproject.toml&query=project.requires-python&style=flat&label=Python&labelColor=%23805959&color=%231F6699">
</p>

**Chiori** - Ядро Disocrd бота, построенное на библиотеке
[hikari](https://github.com/hikari-py/hikari)
для разработки современных модульных ботов, как например **Chioricord**.

**Возможности**:

- **Динамическая загрузка**: Выбирайте только те расширения и функции, которые вам нужны.
- **Обработка ошибок**: Встроенный обработчик ошибок во время работы.
- **Настройки**: Настроить запуск можно просто в `.env` файле.
- **События**: Создавайте и обрабатывайте собственные события.
- **Chio API**: Для разработки своих библиотек и расширений.

Более подробно о ней вы можете прочитать на [сайте](https://chio.miroq.ru).
А подробнее про *Chiori API* можно узнать [здесь](https://chiori.miroq.ru/).

## Установка и запуск

Если вы заинтересовались, то давайте перейдём к запуску Шиори.
Для этого выполните следующие простые шаги:

1. Загрузите репозиторий со всеми компонентами.

```sh
git clone https://git.miroq.ru/chio/cord
```

2. Установите зависимости через [uv](https://astral.sh/uv):

```sh
uv sync -U --with extensions
```

> `--with extensions` означает что мы хотим установить все дополнительные
> зависимости. используемые в расширениях.


3. **Настройки бота для первого запуска.**
   Для этого скопируем файл `env.dist` в `.env`.
   После подставляем токен вашего _Discord_ бота.

```env
BOT_TOKEN = "ODY4MDk..."
```

> Все прочие настройки детально описаны в созданном вами `.env` файле.

4. **Создайте таблицу и пользователя в базе данных Postgres**.
   После этого укажите данные для подключения в `.env` файле.

Теперь всё готово чтобы запустить Шиори через `uv`:

```sh
uv run -m chiori
```

## Архитектура проекта

Бот разработан с использованием _модульной архитектуры_.
Для того чтобы функционал можно было гибко настраивать под свои нужды без лишних усилий.
Это реализуется через **расширения** `extensions/` и **библиотеки** `libs/`.

Структура проекта выглядит следующим образом:

```
├── bot_data/    - Расширения могут читать и записывать файлы сюда.
├── chiori/      - Ядро проекта: Сборка всех компонентов, запуск бота, Chiori API.
├── config/      - Настройки расширений, загружаемые во время запуска бота.
├── extensions/  - Расширения, предоставляющие новый функционал на основе Chiori API.
└── libs/        - Общие компоненты, предоставляющие API для расширений.
```

## Поддержка

Проект распространяется под открытой лицензией.
Если вам понравился проект и вы хотите поддержать его развитие...
Есть несколько способов, как вы можете это сделать:

- Оставить звёздочку в репозитории проекта.
- **Предлагать свои идеи** на форуме или *issue*.
- Участвовать в **бета-тестировании** новых функций на нашем сервере.
- Писать свои собственные **расширения**.

На нашем сервере также есть раздел форума, где вы можете задавать свои вопросы
и принимать активное участие в развитии проекта.

А ещё в Discord сервере вы можете принять участие в **бета-тестировании** новых
функций бота.
И не стесняйтесь сообщать о всех найденных багах, так вы сделаете Шиори лучше.

## Благодарности

При разработке использовались следующие библиотеки:

- [Hikari](https://github.com/hikari-py/hikari):
  A Discord API wrapper for Python and asyncio built on good intentions.

- [Arc](https://github.com/hypergonial/hikari-arc):
  A command handler for hikari with a focus on type-safety and correctness. 

- [miru](https://github.com/hypergonial/hikari-miru):
  A component handler for hikari, inspired by discord.py's views. 

> Также расширения могут использовать свои библиотеки.

Огромная благодарность разработчикам за **чудесные библиотеки**. 🧡
Благодаря общему вкладу мы становимся лучше.
