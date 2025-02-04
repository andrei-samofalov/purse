import typing as t


class CleanSet(set):
    """Set that ignores None"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.discard(None)

    def add(self, __element):
        """Add an element if it is not None"""
        if __element is not None:
            super().add(__element)


class BijectiveMap(dict):
    """Invertible map."""

    def __init__(self, obj: t.Optional[dict[str, str]] = None, **kwargs):
        if obj is None:
            obj = dict()

        obj.update(kwargs)

        formatted = {
            self._normalize_key(k): self._normalize_key(v)
            for k, v in obj.items()
        }
        super().__init__(**formatted)
        self.inverse = {v: k for k, v in formatted.items()}

    def __contains__(self, item: str):
        if not isinstance(item, str):
            return False
        return (
            self._normalize_key(item) in self.keys() or
            self._normalize_val(item) in self.inverse.keys()
        )

    def get(self, __key, __default=None):
        try:
            return self[__key]
        except KeyError:
            try:
                return self.inverse[__key]
            except KeyError:
                if __default is not None:
                    return __default
                raise

    @classmethod
    def _normalize_key(cls, name: str):
        return name.strip().upper()

    @classmethod
    def _normalize_val(cls, name: str):
        return name.strip().title()


@t.runtime_checkable
class _O(t.Protocol):
    pass


ProtocolType = type(_O)
