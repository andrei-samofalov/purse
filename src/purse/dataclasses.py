"""
source:
"""


from dataclasses import Field, fields
from typing import Any, Iterable, TypeGuard, Protocol, ClassVar, AbstractSet


class DataClassProtocol(Protocol):
    """DataClassProtocol implements Protocol interface"""
    __dataclass_fields__: ClassVar[dict[str, Any]]


def extract_dataclass_fields(
    dt: DataClassProtocol,
    exclude: AbstractSet[str] | None = None,
) -> tuple[Field[Any], ...]:
    """Extract dataclass fields.

    Args:
        dt: :class:`DataclassProtocol` instance.
        exclude: An iterable of fields to exclude.

    Returns:
        A tuple of dataclass fields.
    """
    exclude = exclude or set()

    dataclass_fields: Iterable[Field[Any]] = fields(dt)
    if exclude:
        dataclass_fields = (field for field in dataclass_fields if field.name not in exclude)

    return tuple(dataclass_fields)


def extract_dataclass_items(
    dt: DataClassProtocol,
    exclude: AbstractSet[str] | None = None,
) -> tuple[tuple[str, Any], ...]:
    """Extract dataclass name, value pairs.

    Unlike the 'asdict' method exports by the stdlib, this function does not pickle values.

    Args:
        dt: :class:`DataclassProtocol` instance.
        exclude: An iterable of fields to exclude.

    Returns:
        A tuple of key/value pairs.
    """
    dataclass_fields = extract_dataclass_fields(dt, exclude)
    return tuple((field.name, getattr(dt, field.name)) for field in dataclass_fields)


def extract_dataclass_values(
    dt: DataClassProtocol,
    exclude: AbstractSet[str] | None = None,
) -> tuple[Any, ...]:
    """Extract dataclass field values."""
    items = extract_dataclass_items(dt, exclude)
    return tuple(item[1] for item in items)


def simple_asdict(
    obj: DataClassProtocol,
    convert_nested: bool = True,
    exclude: set[str] | None = None,
) -> dict[str, Any]:
    """Convert a dataclass to a dictionary.

    This method has important differences to the standard library version:
    - it does not deepcopy values
    - it does not recurse into collections

    Args:
        obj: :class:`DataclassProtocol` instance.
        convert_nested: Whether to recursively convert nested dataclasses.
        exclude: An iterable of fields to exclude.

    Returns:
        A dictionary of key/value pairs.
    """
    ret: dict[str, Any] = {}
    for field in extract_dataclass_fields(obj, exclude=exclude):
        value = getattr(obj, field.name)
        if is_dataclass_instance(value) and convert_nested:
            ret[field.name] = simple_asdict(value, convert_nested)
        elif isinstance(value, dict):
            val = {}
            for k, v in value.items():
                if is_dataclass_instance(v) and convert_nested:
                    val[k] = simple_asdict(v, convert_nested)
                else:
                    val[k] = v
            ret[field.name] = val
        else:
            ret[field.name] = getattr(obj, field.name)
    return ret


def is_dataclass_instance(obj: Any) -> TypeGuard[DataClassProtocol]:
    """Check if an object is a dataclass instance.

    Args:
        obj: An object to check.

    Returns:
        True if the object is a dataclass instance.
    """
    return hasattr(type(obj), "__dataclass_fields__")  # pyright: ignore[reportUnknownArgumentType]
