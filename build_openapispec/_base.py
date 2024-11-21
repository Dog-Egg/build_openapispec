import typing as t
from collections import UserDict, defaultdict
from collections.abc import Mapping
from functools import partial
from inspect import cleandoc
from types import SimpleNamespace


class Empty:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance


empty = Empty()


class Field:
    def __init__(self, *, default: t.Any = empty, transform=None):
        self.default = default
        self.transform: t.Callable[[t.Any], t.Any] = transform or (lambda x: x)


class Schema(Mapping):
    __declare_fields__: t.Dict[str, Field] = {}

    def __init__(self, fields=None, /) -> None:
        data = {}
        if fields:
            data.update(fields)

        self.__fields = {}
        for k, v in data.items():
            if v is empty:
                continue

            if k in self.__declare_fields__:
                f = self.__declare_fields__[k]
                if f.default is v:
                    continue
                v = f.transform(v)

            self.__fields[k] = v

        self.__hash = object()

    def __getitem__(self, name):
        return self.__fields[name]

    def __iter__(self):
        return iter(self.__fields)

    def __len__(self):
        return len(self.__fields)

    def __hash__(self) -> int:
        return hash(self.__hash)

    def __repr__(self) -> str:
        return repr(self.__fields)


class Root:
    pass


class OpenAPIObject(Schema, Root):
    pass


class InfoObject(Schema):
    __declare_fields__ = {
        "description": Field(transform=cleandoc),
    }


class PathItemObject(Schema):
    __declare_fields__ = {
        "description": Field(transform=cleandoc),
    }


class OperationObject(Schema):
    __declare_fields__ = {
        "description": Field(transform=cleandoc),
        "deprecated": Field(default=False),
    }


class ParameterObject(Schema):
    __declare_fields__ = {
        "required": Field(default=False),
        "description": Field(transform=cleandoc),
        "deprecated": Field(default=False),
    }


class RequestBodyObject(Schema):
    __declare_fields__ = {
        "required": Field(default=False),
        "description": Field(transform=cleandoc),
    }


class ResponseObject(Schema):
    __declare_fields__ = {
        "description": Field(transform=cleandoc),
    }


class MediaTypeObject(Schema):
    pass


class TagObject(Schema):
    __declare_fields__ = {
        "description": Field(transform=cleandoc),
    }


class SchemaObject(Schema):
    __declare_fields__ = {
        "description": Field(transform=cleandoc),
        "readOnly": Field(default=False),
        "writeOnly": Field(default=False),
        "uniqueItems": Field(default=False),
        "nullable": Field(default=False),
        "exclusiveMaximum": Field(default=False),
        "exclusiveMinimum": Field(default=False),
    }

    def __init__(self, *args, key=None) -> None:
        super().__init__(*args)
        self.key = key


class SecuritySchemeObject(Schema):
    __declare_fields__ = {
        "description": Field(transform=cleandoc),
    }

    def __init__(self, *args, key: str) -> None:
        super().__init__(*args)
        self.key = key


class SecurityRequirementObject(Schema):

    def __init__(self, *args, scheme: SecuritySchemeObject) -> None:
        self.scheme = scheme
        super().__init__({scheme.key: []})


class OpenAPISpecNamespace(SimpleNamespace):
    def __init__(self, version: str, **kwargs: t.Any) -> None:
        super().__init__(
            version=version,
            empty=empty,
            non_empty=non_empty,
            build=partial(build, version),
            **kwargs,
        )


def count_references(data):
    references: t.Dict[SchemaObject, int] = defaultdict(int)
    visited: t.Set[SchemaObject] = set()

    def count_recursive(data):
        if isinstance(data, Mapping):
            if isinstance(data, SchemaObject):
                references[data] += 1
                if data in visited:
                    return  # 避免重复引用计数
                visited.add(data)
            for value in data.values():
                count_recursive(value)
        elif isinstance(data, list):
            for value in data:
                count_recursive(value)

    count_recursive(data)
    return references


class Components(UserDict):
    def setfield(self, field: str, key: str, value):
        values = self.setdefault(field, {})
        values[key] = value


def build(version, openapi, /):
    assert isinstance(openapi, Root)

    # schema count
    ref_count = count_references(openapi)

    tags = {}
    components = Components()

    def dumps(data):
        if isinstance(data, Mapping):
            if isinstance(data, Schema):
                # schema object
                if isinstance(data, SchemaObject):
                    if data.key and ref_count[data] > 1:
                        components.setfield("schemas", data.key, dumps(dict(data)))
                        return {"$ref": "#/components/schemas/%s" % data.key}

                # security scheme
                if isinstance(data, SecurityRequirementObject):
                    scheme = data.scheme
                    components.setfield("securitySchemes", scheme.key, dict(scheme))

            return {k: dumps(v) for k, v in data.items()}

        if isinstance(data, list):
            return [dumps(v) for v in data]

        return data

    rv: dict = dumps(openapi)  # type: ignore
    rv["openapi"] = version
    if components:
        rv["components"] = dict(components)
    return rv


def openapispec(version: str, /):
    assert version in ("3.0.3",)
    return OpenAPISpecNamespace(
        version=version,
        OpenAPIObject=OpenAPIObject,
        InfoObject=InfoObject,
        PathItemObject=PathItemObject,
        OperationObject=OperationObject,
        ParameterObject=ParameterObject,
        ResponseObject=ResponseObject,
        SchemaObject=SchemaObject,
        MediaTypeObject=MediaTypeObject,
        TagObject=TagObject,
        SecuritySchemeObject=SecuritySchemeObject,
        SecurityRequirementObject=SecurityRequirementObject,
        RequestBodyObject=RequestBodyObject,
    )


def non_empty(a, b=None, /):
    if a is b:
        return empty
    return a
