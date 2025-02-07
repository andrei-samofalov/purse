import asyncio
from configparser import ConfigParser

import purse


async def main():
    config = ConfigParser()
    config.read('config.ini')
    bot_config = config['bot']

    logger = purse.logging.setup(
        telegram_setup=purse.logging.TelegramSetup(
            bot=purse.logging.SimpleLoggingBot(token=bot_config.get('token')),
            log_chat_id=bot_config.get('log_chat_id'),
            send_delay=bot_config.getint('send_delay', fallback=1),
            logger_level=bot_config.getint('logger_level', fallback=0),
            logger_name=bot_config.getint('logger_name',
                                          fallback=purse.logging.get_default_logger_name()),
            service_name=bot_config.get('service_name', fallback="purse"),
        ),
    )

    kill_event = purse.signals.setup()
    logger.info('app is up')
    logger.debug(f'hello!', to_dev=True)
    logger.to_dev('dev message')  # goes only to telegram

    try:
        1 / 0
    except ZeroDivisionError as e:
        logger.exception(e)

    logger.error('error!')

    await kill_event.wait()
    logger.info('app is down')


if __name__ == '__main__':
    asyncio.run(main())
