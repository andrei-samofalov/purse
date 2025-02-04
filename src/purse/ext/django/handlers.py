import sys

from django.core.exceptions import RequestDataTooBig
from django.core.handlers.asgi import (
    ASGIRequest as DjangoASGIRequest,
    ASGIHandler as DjangoASGIHandler,
)
from django.core.handlers.wsgi import (
    WSGIRequest as DjangoWSGIRequest,
    WSGIHandler as DjangoWSGIHandler,
)
from django.http.response import HttpResponseBadRequest, HttpResponse

from purse.logging import logger_factory

logger = logger_factory("django.request", include_project=True)


class PurseWSGIRequest(DjangoWSGIRequest):
    def __init__(self, app, environ):
        super().__init__(environ)
        self._app = app

    app: "PurseWSGIHandler" = property(lambda self: self._app)


class PurseWSGIHandler(DjangoWSGIHandler):
    request_class = PurseWSGIRequest

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._storage = {}

    def __setitem__(self, key, value):
        self._storage[key] = value

    def __getitem__(self, key):
        return self._storage[key]


class PurseASGIRequest(DjangoASGIRequest):
    """
    Custom request subclass that decodes from an ASGI-standard request dict
    and wraps request body handling.
    """

    # Number of seconds until a Request gives up on trying to read a request
    # body and aborts.
    body_receive_timeout = 60

    def __init__(self, app, scope, body_file):
        super().__init__(scope, body_file)
        self._app: "PurseASGIHandler" = app

    app: "PurseASGIHandler" = property(lambda self: self._app)


class PurseASGIHandler(DjangoASGIHandler):
    request_class = PurseASGIRequest

    def __init__(self):
        super().__init__()
        self._storage = {}

    def __setitem__(self, key, value):
        self._storage[key] = value

    def __getitem__(self, key):
        return self._storage[key]

    def create_request(self, scope, body_file):
        """
        Create the Request object and returns either (request, None) or
        (None, response) if there is an error response.
        """
        try:
            return self.request_class(self, scope, body_file), None
        except UnicodeDecodeError:
            logger.warning(
                "Bad Request (UnicodeDecodeError)",
                exc_info=sys.exc_info(),
                extra={"status_code": 400},
            )
            return None, HttpResponseBadRequest()
        except RequestDataTooBig:
            return None, HttpResponse("413 Payload too large", status=413)
