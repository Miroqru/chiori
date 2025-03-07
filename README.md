# ChioriCord

![](/assets/chioricord_banner_nobg.png)

<p align="center">
    <img alt="license" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fcodeberg.org%2FSalormoon%2Fchioricord%2Fraw%2Fbranch%2Fmain%2Fpyproject.toml&query=tool.poetry.license&label=license&color=red">
    <img alt="Gitea Last Commit" src="https://img.shields.io/gitea/last-commit/Salormoon/chioricord?gitea_url=https%3A%2F%2Fcodeberg.org">
    <img alt="version" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fcodeberg.org%2FSalormoon%2Fchioricord%2Fraw%2Fbranch%2Fmain%2Fpyproject.toml&query=tool.poetry.version&prefix=v&label=version&color=green">
    <img alt="Python version" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fcodeberg.org%2FSalormoon%2Fchioricord%2Fraw%2Fbranch%2Fmain%2Fpyproject.toml&query=tool.poetry.dependencies.python&label=python&color=blue">
    <img alt="Discord" src="https://img.shields.io/discord/1282356859595919463?logo=discord&label=Discord&color=%230066ff">
    <a href="https://github.com/astral-sh/ruff"><img alt="Ruff" src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json"></a>
</p>

> Многофункциональный модульный дискорд бот для **вашего** лампового сервера.

**Возможности Чиори**:

- **Множество мини-игр**: **Сапёр**, крестики-нолики, найди пару и другие.
- Маленькие **утилиты**: Подбросить кубик, информация о цвете, аватар пользователя.
- **Системные** команды, по типу `/help`, чтобы подробнее узнать о боте.
- Коллекция библиотек для создания более масштабных игр. (*в процессе*).
- *Тут могут быть ваши функции...*

> Возрождение проекта **Chiori** lab.
> На этот раз для **Discord** серверов.


## Установка и первый запуск

1. Клонируем репозиторий со всеми компонентами.

```sh
git clone https://codeberg.org/Salormoon/chioricord
```

2. Устанавливаем зависимости через [poetry](https://python-poetry.org):

```sh
poetry install
```

3. **Настраиваем бота для первого запуска.**
  Для этого скопируем файл `env.dist` в `.env`.
  После подставляем токен вашего *Discord* бота.

```env
BOT_TOKEN = "ODY4MDk..."
```

Теперь всё готово чтобы запустить Чиори через `poetry`:

```sh
poetry run python -m chioricord
```

## Структура проекта

Бот разработан с использованием модульной структуры.
Чтобы вам самостоятельно регулировать функционал бота, достаточно перемещать
файлы в `extensions/`.

К примеру если вам не нужен какой-то плагин, просто переместите его в другую
директорию.

> Обратите внимание что для работы некоторый расширений требуются другие
> расписания и библиотеки.
>
> Так например, для работы экономики (`coinengine`) требуется расширение
> `coins`.

```
├── assets     - Некоторые медиафайлы репозитория (документация?)
├── chioricord - Ядро бота: загрузчик плагинов, хранилище настроек.
├── extensions - Расширения, предоставляющие больше возможностей для бота.
└── libs       - Общие модули, используемые разными расширениями.
```

## Поддержка бота

Есть несколько вариантов, как вы можете помочь развитию бота:

- Помочь проекту, **предлагая свои идеи**.
- Участвовать в **бета-тестировании** бота.
- Писать свои собственные **расширения**.

Предлагать свои **собственные идеи** вы можете как в `issue`, так и в
соответствующем **разделе форуме** в Discord сервера (ссылка выше).

На этом же сервере вы можете принять участие в **бета-тестировании** новых
функций бота.
И не стесняйтесь сообщать о всех найденных багах в проекте.

Если вы разработчик, то вы можете как использовать наработки данного бота, так
и писать свои собственные плагины для этой платформы.
Давайте все вместе сделаем лучшего Discord бота с открытым исходным кодом.


## Настройки бота

На данный момент все настройки бота хранятся в одном `.env` файле.
Это так называемый *корневой файл настроек*, который загружается вместе с ботом.
Тут указаны все необходимые для работы ядра параметры.

- `BOT_TOKEN`: **Токен для запуска бота**.
  Укажите токен от вашего Discord бота чтобы запустить **ChioriCord**.
- `BOT_OWNER`: **Владелец бота**.
  Укажите здесь ID владельца бота.
  На владельца не распространяются ограничения бота.
  А также владелец имеет доступ ко всем системным командам управления бота.

В будущих обновлениях появится хранилище настроек плагинов, а также гибкая
система прав доступа, привязанная к ролям.
