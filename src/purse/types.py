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


@t.runtime_checkable
class _O(t.Protocol):
    pass


ProtocolType = type(_O)
