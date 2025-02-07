# python‑purse

**python‑purse** is a library that collects a variety of snippets and utilities for both
asynchronous and synchronous Python projects. Whether you're building bots, web applications,
or other tools, this library provides ready-to-use code modules to speed up development.

## Features

- **Dataclasses Utilities**  
  Enhance your work with Python dataclasses with extra helpers and shortcuts.

- **Datetime Helpers**  
  Tools for common datetime operations.

- **HTTP Clients**  
  Built-in support for multiple HTTP clients including `httpx`, `requests`, and builtin http module.

- **Framework Extensions**
    - **aiogram**: Bootstrap modules, decorators, routers, and utilities for Telegram bots.
    - **aiohttp**: Simplified app creation and server utilities.
    - **django**: ASGI/WSGI handlers, repository patterns, and more for Django projects.

- **Logging**  
  Custom logging configurations and integrations (including Telegram-based logging).
  ```python
  config = ConfigParser()
  config.read('config.ini')
  bot_config = config['bot']
    
  purse.logging.setup(
    telegram_setup=TelegramSetup(
        bot=logging.SimpleLoggingBot(token=bot_config.get('token')),
        log_chat_id=bot_config.get('log_chat_id'),
        send_delay=bot_config.getint('send_delay'),
        logger_level=bot_config.getint('logger_level'),
        service_name=bot_config.get('service_name'),
    ),
  )
  ```

- **Interfaces and Repositories**  
  Protocol definitions and in-memory repository implementations for fast prototyping.

- **JSON and Functional Helpers**  
  Utility functions to simplify JSON handling and functional programming patterns.

- **Additional Utilities**  
  Signal handling, system-level helpers, type utilities, and more.

## Installation

If **python‑purse** is published on PyPI, you can install it via pip:

```bash
pip install python-purse
```

Or, with extras:
```bash
pip install python-purse[aiogram]
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

