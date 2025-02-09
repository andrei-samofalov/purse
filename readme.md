# python‑purse

**python‑purse** is a library that collects a variety of snippets and utilities for both
asynchronous and synchronous Python projects. Whether you're building bots, web applications,
or other tools, this library provides ready-to-use code modules to speed up development.

## Framework Extensions

- **aiogram**: Bots and dp bootstrap, router-makers, useful decorators and utilities for Telegram bots.
- **aiohttp**: Simplified app creation and server utilities.
- **django**: ASGI/WSGI handlers, repository patterns, and more for Django projects.

## Logging

Custom logging configurations and integrations (including Telegram-based logging).

```python
from configparser import ConfigParser

import purse.logging

config = ConfigParser()
config.read('config.ini')
bot_config = config['bot']

tg_logger = purse.logging.setup(
    telegram_setup=purse.logging.TelegramSetup(
        bot=purse.logging.SimpleLoggingBot(token=bot_config.get('token')),
        log_chat_id=bot_config.get('log_chat_id'),
        send_delay=bot_config.getint('send_delay'),
        logger_level=bot_config.getint('logger_level'),
        service_name=bot_config.get('service_name'),
    ),
)

tg_logger.debug("dev message", to_dev=True)  # prints to stderr and sends message to telegram

try:
    raise Exception("some exception")
except Exception as exc:
    tg_logger.exception(exc)  # prints traceback to stderr and sends message to telegram

    
from logging import getLogger

your_app_logger = getLogger("app")
your_app_logger.error('error in runtime')  # prints to stderr and sends message to telegram

```
You don't have to use `purse.logging.setup` function return object (`tg_logger` in example above) 
directly for error/exception telegram logging unless you want to send messages 
by `TelegramLogger.to_tg(...)` and `TelegramLogger.to_dev(...)` methods.


## Interfaces and Repositories

Protocol definitions and in-memory repository implementations for fast prototyping and testing.

## JSON encoders and decoders

Utility functions and classes to simplify JSON handling (mostly decoding and encoding Decimals,
UUIDs, dates, and other specific types).

```python
from purse import json as purse_json
from decimal import Decimal

purse_json.dumps({"val": Decimal("100")})  # '{"val": "100"}'
purse_json.loads('{"val": "100"}')  # {'val': Decimal('100')}

```

## Asyncio signals handling

Easy loop signal setup for SIGINT and SIGTERM.
Use predefined `purse.signals.prepare_shutdown` (internal flag of this event would be set to True
when one of signals received) and `purse.signals.shutdown_complete` events in your code for more
compatability.

```python 
import purse
import asyncio 

async def main():
  kill_event = purse.signals.setup()
  ... # some startup logic
  
  await kill_event.wait()
  ... # some shutdown logic
  await purse.signals.shutdown_complete.wait()
  

if __name__ == '__main__':
    asyncio.run(main())
```

You can pass your custom function to `purse.signals.setup` for handling signals. This function
must have exact two arguments: `signal.Signals` and `asyncio.Event` (internal flag of this event
you must set to True due the function execution).

## Installation

You can install **python-purse** via pip (or with your another favorite manager) from PyPi:

```bash
pip install python-purse
```

## Contributing

Contributions are welcome! If you’d like to contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch (git checkout -b feature/my-feature).
3. Commit your changes (git commit -am 'Add new feature').
4. Push your branch (git push origin feature/my-feature).
5. Open a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contacts

[email](mailto:andrei.e.samofalov@gmail.com)

[telegram](https://t.me/samofalov_andrey)

