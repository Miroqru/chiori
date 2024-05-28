"""Скрипт для запуска бота.

Для запуска бота используйте следующую команду.

.. code-block:: shell

    python -m chioricord

Author: Milinri Nirvalen
"""

import asyncio

from chioricord.bot import start_bot

if __name__ == "__main__":
    asyncio.run(start_bot())
