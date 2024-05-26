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

Многофункциональный дискорд бот для **вашего** сервера.

**Что умеет этот бот**:

- Общение с **GPT**.
- *Тут могут быть ваши функции.*


## Установка

1. Клонируйте репозиторий.

```sh
git clone https://codeberg.org/Salormoon/chioricord
```

2. Установите зависимости через poetry:

```sh
poetry install
```

3. **Настройте бота для работы.**
  Для этого скопируйте файл `env.dist` в `.env`.
  После подставьте ваш токен от discord бота.

```toml
BOT_TOKEN = "ODY4MDk..."
```

Теперь всё готово чтобы запустить этого бота чезе poetry:

```sh
poetry run python -m chioricord
```

## Структура проекта

```
├── assets      - Некоторые медиафайлы репозитория
├── chioricord  - Ядро бота и загрузчика когов
├── cogs        - Опциональные ресширения для бота
└── libs        - Некоторые общие модули, которые можно использовать между разными когами
```
