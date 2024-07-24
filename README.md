# ChioriCord

> Возрождение проекта Chiori.
> На этот раз для **Discord** серверов.

![](/assets/chioricord_banner_nobg.png)


<p align="center">
    <img alt="license" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fcodeberg.org%2FSalormoon%2Fchioricord%2Fraw%2Fbranch%2Fmain%2Fpyproject.toml&query=tool.poetry.license&label=license&color=red">
    <img alt="Gitea Last Commit" src="https://img.shields.io/gitea/last-commit/Salormoon/chioricord?gitea_url=https%3A%2F%2Fcodeberg.org">
    <img alt="version" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fcodeberg.org%2FSalormoon%2Fchioricord%2Fraw%2Fbranch%2Fmain%2Fpyproject.toml&query=tool.poetry.version&prefix=v&label=version&color=green">
    <img alt="Python version" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fcodeberg.org%2FSalormoon%2Fchioricord%2Fraw%2Fbranch%2Fmain%2Fpyproject.toml&query=tool.poetry.dependencies.python&label=license&color=blue">
    <img alt="Discord" src="https://img.shields.io/discord/1105813801997189160?logo=discord&label=Discord&color=%230066ff">
</p>

Многофункциональный дискорд бот с модульной структурой для **вашего** сервера.

**Что умеет этот бот**:

- Игра **Сапёр**, **Крестики-нолики**.
- Подбросить кубики.
- Общение с **GPT**.
- Получить информацию о цвете.
- Разные маленькие команды.
- *Тут могут быть ваши функции.*


## Установка

1. Клонируйте репозиторий.

```sh
git clone https://codeberg.org/Salormoon/chioricord
```

2. Установите зависимости через [poetry](https://python-poetry.org):

```sh
poetry install
```

3. **Настройте бота для работы.**
  Для этого скопируйте файл `env.dist` в `.env`.
  После подставьте ваш токен от discord бота.

```toml
BOT_TOKEN = "ODY4MDk..."
```

Теперь всё готово чтобы запустить этого бота чезе `poetry`:

```sh
poetry run python -m chioricord
```

## Структура проекта

Бот разработан с использованием модельной структуры.
Чтобы вам самостоятельно регулировать функционал бота, достаточно перемещать
файлы в `exstensions/`.

```
├── assets      - Некоторые медиафайлы репозитория (документация?)
├── chioricord  - Ядро бота: загрузчик плагинов, хранилище настроек.
├── cogs        - Расширения, предоставляющие больше возможностей для бота.
└── libs        - Общие модули, используемые разными расширениями.
```

## Настройки бота

На данный момент все настройки бота хранятся в одном `.env` файле.
Это так называемый корневой файл настроек, который загружается вместе с ботом.
Тут указаны все необходимые для работы ядра параметры.


- `BOT_TOKEN`: **Токен для запуска бота**.
  Укажите токен от вашего Discord бота чтобы запустить **ChioriCord**.
- `BOT_OWNER`: **Вледелец бота**.
  Укажите здесь ID владельца бота.
  На владельца не распространяются ограничения бота.
  А также владелец имете доступ ко всем системным командам управления бота.

В будущих обновлениях появится хранилище настроек плагинов, а также гибкая
систама прав доступа, привязанная к ролям.
