import django
from purse.ext.django.handlers import PurseASGIHandler


def get_asgi_application(**appkwargs):
    """
    The public interface to Django's ASGI support. Return an ASGI 3 callable.

    Avoids making django.core.handlers.ASGIHandler a public API, in case the
    internal implementation changes or moves in the future.
    """
    django.setup(set_prefix=False)
    app = PurseASGIHandler()
    for k, v in appkwargs.items():
        app[k] = v
    return app
