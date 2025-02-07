from purse.imports import ensure_installed

from . import bot as bot
from . import commands as commands
from . import polling as polling
from . import webhook as webhook

ensure_installed("aiogram")
