from aiogram.filters import Command
from aiogram.types import BotCommand


def make_command_filter(name: str, *commands: BotCommand) -> type[Command]:
    """Create command-filter"""
    return type(Command)(
        name,
        (Command,),
        {"__init__": lambda self: Command.__init__(self, *commands)},
    )


HELP_COMMAND = BotCommand(command='help', description='Show help')
HelpCommand = make_command_filter("HelpCommand", HELP_COMMAND)
