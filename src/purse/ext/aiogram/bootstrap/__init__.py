from purse.imports import ensure_installed

from . import (
    bot as bot,
    commands as commands,
    polling as polling,
    webhook as webhook,
)

ensure_installed("aiogram")
