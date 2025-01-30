import decimal
import json
import uuid
from datetime import datetime, date, time


class JSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time, decimal types, and
    UUIDs.
    """

    def default(self, o):
        if isinstance(o, datetime):
            r = o.isoformat()
            if o.microsecond:
                r = r[:23] + r[26:]
            if r.endswith("+00:00"):
                r = r.removesuffix("+00:00") + "Z"
            return r
        elif isinstance(o, date):
            return o.isoformat()
        elif isinstance(o, time):
            r = o.isoformat()
            if o.microsecond:
                r = r[:12]
            return r

        elif isinstance(o, (decimal.Decimal, uuid.UUID)):
            return str(o)
        else:
            return super().default(o)
