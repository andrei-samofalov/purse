import asyncio

from purse import logging
from purse import signals
from purse.logging import TelegramSetup

logger = logging.default_logger


async def main():
    logging.setup(
        telegram_setup=TelegramSetup(
            bot=logging.SimpleLoggingBot(token='6959549185:AAEFx81Jsr6sZ8mE3llriaFLgnrlV372Tmo'),
            log_chat_id=436350071,
            service_name='purse'
        ),
    )

    kill_event = signals.setup()
    logger.info(f'app is up')

    await kill_event.wait()
    logger.info(f'app is down')


if __name__ == '__main__':
    asyncio.run(main())
