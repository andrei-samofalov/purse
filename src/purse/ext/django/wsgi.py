import django

from purse.ext.django.handlers import PurseWSGIHandler


def get_wsgi_application(**appkwargs):
    """
    The public interface to Django's WSGI support. Return a WSGI callable.

    Avoids making django.core.handlers.WSGIHandler a public API, in case the
    internal WSGI implementation changes or moves in the future.
    """
    django.setup(set_prefix=False)
    app = PurseWSGIHandler()
    for k, v in appkwargs.items():
        app[k] = v
    return app
