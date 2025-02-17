import asyncio
from configparser import ConfigParser

import purse
from purse.aiotasks import Example


class s:
    def __init__(self):
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    def create_task(self, coro):
        stop = asyncio.Event()
        async def _wrapper():
            while not stop.is_set():
                try:
                    await coro(stop)
                except asyncio.CancelledError:
                    stop.set()

        asyncio.create_task(_wrapper())


    async def _wrap_worker(self, w_coro, stop):
        while not stop.is_set():
            try:
                await asyncio.shield(w_coro)
            except asyncio.CancelledError:
                stop.set()

    async def _worker(self, stop):
        while not stop.is_set():
            try:
                await asyncio.sleep(2)
                print('hello!')

            except asyncio.CancelledError:
                print('canceled! by CancelledError')
        else:
            print('canceled! in loop')

    def start(self):
        stop = asyncio.Event()
        self._task = asyncio.create_task(
            self._wrap_worker(self._worker(stop), stop)
        )

    async def stop(self):
        self._task.cancel()
        await self._stop_event.wait()
        try:
            await self._task  # Даем воркеру доработать до конца
        except asyncio.CancelledError:
            pass  # Ожидаем завершения без исключения


async def main():
    config = ConfigParser()
    config.read('config.ini')
    bot_config = config['bot']

    logger = purse.logs.setup(
        telegram_setup=purse.logs.TelegramSetup(
            bot=purse.logs.SimpleLoggingBot(token=bot_config.get('token')),
            log_chat_id=bot_config.get('log_chat_id'),
            send_delay=bot_config.getint('send_delay', fallback=1),
            logger_level=bot_config.getint('logger_level', fallback=0),
            logger_name=bot_config.getint('logger_name',
                                          fallback=purse.logs.get_default_logger_name()),
            service_name=bot_config.get('service_name', fallback="purse"),
        ),
    )

    kill_event = purse.signals.setup()
    logger.info('app is up')

    e = Example()
    e.start()
    await asyncio.sleep(0.1)
    e.stop()

    await kill_event.wait()
    logger.info('app is down')


if __name__ == '__main__':
    asyncio.run(main())
