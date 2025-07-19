# ChioriCord

<p align="center">
  <img src="https://miroq.ru/chio/images/chio.png" width=256>
</p>

<p align="center">
  <a href="https://github.com/astral-sh/ruff"><img alt="Ruff" src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json"></a>
  <img alt="Version" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fgit.miroq.ru%2Fsalormoon%2Fchioricord%2Fraw%2Fbranch%2Fmain%2Fpyproject.toml&query=project.version&prefix=v&style=flat&label=Chiori&labelColor=%23B38B74&color=%232185A6">
  <img alt="LICENSE" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fgit.miroq.ru%2Fsalormoon%2Fchioricord%2Fraw%2Fbranch%2Fmain%2Fpyproject.toml&query=project.license&style=flat&label=License&labelColor=%23B38B74&color=%2317B34B">
  <img alt="Discord" src="https://img.shields.io/discord/1282356859595919463?style=flat&label=Salor%3B%20land&labelColor=%23B38B74&color=%2373FFAD">
  <img alt="Docs" src="https://img.shields.io/badge/Miroq-docs?style=flat&label=Docs&labelColor=%23805959&color=%23B32D8A&link=https%3A%2F%2Fmiroq.ru%2Fchio%2F">
  <img alt="Python" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fgit.miroq.ru%2Fsalormoon%2Fchioricord%2Fraw%2Fbranch%2Fmain%2Fpyproject.toml&query=project.requires-python&style=flat&label=Python&labelColor=%23805959&color=%231F6699">
  <img alt="Gitea Last Commit" src="https://img.shields.io/gitea/last-commit/salormoon/chioricord?gitea_url=https%3A%2F%2Fgit.miroq.ru&style=flat&labelColor=%23805959&color=%23F68121">

</p>

> Многофункциональный модульный дискорд бот для **вашего** лампового сервера.

**Основные возможности**:

- **Множество мини-игр**: **Сапёр**, крестики-нолики, найди пару и ешё 6 игр.
- **Модульная система плагинов**: Выбирайте только то что вам нужно.
  Управляйте своими плагинами и настройками бота.
- **Поощрение активности участников**: Уровни за активность, статистика
  участника. Сколько сообщений/слов/времени в голосовом канале.
  События при получении нового уровня.
- **Общение с ИИ**: OpenAI API и все модели что их поддерживают.
- **Музыкальный плеер**: на основе Lavalink v4. Множество источников.
  Очередь воспроизведения.
- **РП команды**: Обнимашки и целовашк.
- **Прочие весёлые команды**: Статус майнкрафт сервера, коробка с весёлостями.
- **Коллекция библиотек**: Экономика, инвентарь, активность пользователя и
  другие. Для расширения функционала плагинов.
- _Тут могут быть ваши функции..._

> Возрождение проекта **Chiori** _lab_ На этот раз для **Discord** серверов.

## Установка и первый запуск

Благодаря открытому коды вы можете использовать Шиори для своих серверов.
Для этого вам понадобится:

1. Клонируйте репозиторий со всеми компонентами.

```sh
git clone https://git.miroq.ru/salormoon/chioricord
```

2. Установите зависимости через [uv](https://astral.sh/uv):

```sh
uv sync
```

Если же вы хотите использовать **все** возможности Шиори, то выполните:

```sh
uv sync --all-groups
```

3. **Настройки бота для первого запуска.**
   Для этого скопируем файл `env.dist` в `.env`.
   После подставляем токен вашего _Discord_ бота.

```env
BOT_TOKEN = "ODY4MDk..."
```

4. **Создайте таблицу и пользователя в базе данных Postgres**.
   После этого укажите данные для подключения в `.env` файле.

Теперь всё готово чтобы запустить Чиори через `uv`:

```sh
uv run -m chioricord
```

## Структура проекта

Бот разработан с использованием _модульной структуры_.
Для того чтобы вам регулировать функционал бота, достаточно перемещать
файлы в `extensions/`.

Если вам не нужен какой-то плагин - удалить его.

> Обратите внимание что для работы некоторый расширений **требуются** другие
> _расширения и библиотеки_.
>
> Так например, для работы экономики (`coinengine`) требуется расширение
> `coins`.

```
├── chioricord - Ядро бота: загрузчик расширений, хранилище настроек, база данных.
├── extensions - Расширения, предоставляющие больше возможностей для бота.
└── libs       - Общие модули, предоставляющие API для расширений.
```

## Поддержка бота

Есть несколько вариантов, как вы можете помочь развитию бота:

- **Предлагать свои идеи**.
- Участвовать в **бета-тестировании** новых функций.
- Писать свои собственные **расширения**.

Предлагать свои **собственные идеи** вы можете как в `issue`, так и в
соответствующем **разделе форуме** в Discord сервера (ссылка выше).

На этом же сервере вы можете принять участие в **бета-тестировании** новых
функций бота.
И не стесняйтесь сообщать о всех найденных багах.

Если вы разработчик, то вы можете попробовать написать своё расширения для бота.
Давайте все вместе сделаем **лучшего Discord бота** с открытым исходным кодом.
