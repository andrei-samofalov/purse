from purse.imports import ensure_installed

from . import (
    utils as utils,
    bot as bot,
    commands as commands,
    decorators as decorators,
    polling as polling,
    webhook as webhook,
)

ensure_installed("aiogram")
