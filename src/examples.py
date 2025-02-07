import asyncio
from configparser import ConfigParser

from purse import logging
from purse import signals
from purse.logging import TelegramSetup


async def main():
    config = ConfigParser()
    config.read('config.ini')
    bot_config = config['bot']

    logger = logging.default_logger
    logging.setup(
        telegram_setup=TelegramSetup(
            bot=logging.SimpleLoggingBot(token=bot_config.get('token')),
            log_chat_id=bot_config.get('log_chat_id'),
            send_delay=bot_config.getint('send_delay'),
            logger_level=bot_config.getint('logger_level'),
            service_name=bot_config.get('service_name'),
        ),
    )

    kill_event = signals.setup()
    logger.info('app is up')

    logger.error('error!')

    await kill_event.wait()
    logger.info('app is down')


if __name__ == '__main__':
    asyncio.run(main())
