import asyncio

from purse import logging
from purse import signals


logger = logging.default_logger


async def main():
    logging.setup(
        telegram_handler_provider=lambda: logging.TelegramHandler(
            bot=logging.SimpleLoggingBot(token='6959549185:AAEFx81Jsr6sZ8mE3llriaFLgnrlV372Tmo'),
            notify_chat_id=436350071,
            service_name='asutils',
        ),
    )

    kill_event = signals.setup()
    logger.info(f'app is up')

    try:
        1 / 0
    except ZeroDivisionError as e:
        logger.exception(e)

    await kill_event.wait()
    logger.info(f'app is down')


if __name__ == '__main__':
    asyncio.run(main())
