import datetime
import decimal
import functools
import json as jsonlib
import re
import typing as t
import uuid

_T = t.TypeVar('_T')


def _try_parse_decimal(s: _T) -> decimal.Decimal | _T:
    try:
        return decimal.Decimal(s)
    except decimal.InvalidOperation:
        return s


def _try_parse_uuid(s: _T) -> uuid.UUID | _T:
    try:
        return uuid.UUID(s)
    except (ValueError, AttributeError):
        print(f'Failed to parse UUID: {s}')
        return s


uuid_regex = re.compile(
    r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$'
)


class PurseJSONDecoder(jsonlib.JSONDecoder):
    """
    Decode JSON that includes serialized ``Decimal`` and ``UUID`` instances.
    """

    def parse(self, obj: t.Any) -> t.Any:
        """Try to parse Decimals and UUIDs"""
        if isinstance(obj, str):
            if re.match(uuid_regex, obj):
                return _try_parse_uuid(obj)
            return _try_parse_decimal(obj)
        if isinstance(obj, dict):
            for key, val in obj.items():
                obj[key] = self.parse(val)
            else:
                return obj
        if isinstance(obj, t.Iterable):
            return [self.parse(val) for val in obj]
        return obj

    def decode(self, s, **kwargs):
        """Return the Python representation of ``s`` (a ``str`` instance
        containing a JSON document)."""
        pre = super().decode(s, **kwargs)
        return self.parse(pre)


class PurseJSONEncoder(jsonlib.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time, decimal types, and
    UUIDs.
    mostly taken from source: django.core.serializers.json.DjangoJSONEncoder
    """

    def default(self, o):
        if isinstance(o, datetime.datetime):
            r = o.isoformat()
            if o.microsecond:
                r = r[:23] + r[26:]
            if r.endswith("+00:00"):
                r = r.removesuffix("+00:00") + "Z"
            return r
        elif isinstance(o, datetime.date):
            return o.isoformat()
        elif isinstance(o, datetime.time):
            if o.utcoffset() is not None:
                raise ValueError("JSON can't represent timezone-aware times.")
            r = o.isoformat()
            if o.microsecond:
                r = r[:12]
            return r
        elif isinstance(o, (decimal.Decimal, uuid.UUID)):
            return str(o)
        else:
            return super().default(o)


dumps = functools.partial(jsonlib.dumps, cls=PurseJSONEncoder)
loads = functools.partial(jsonlib.loads, cls=PurseJSONDecoder)
