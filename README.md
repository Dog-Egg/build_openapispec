# build-openapispec

为构建 OAS 提供一些便利，如自动将多次引用的 Schema Object 转为 Reference Object。

```python
from build_openapispec import openapispec

oas = openapispec("3.0.3")


foo = oas.SchemaObject(
    {
        "type": "string",
    },
    key="foo",
)

bar = oas.SchemaObject(
    {
        "type": "array",
        "items": foo,
    },
    key="bar",
)

assert oas.build(
    oas.OpenAPIObject(
        {
            "info": oas.InfoObject(
                {
                    "title": "API Document",
                    "version": "0.1.0",
                }
            ),
            "paths": {
                "/": oas.PathItemObject(
                    {
                        "get": oas.OperationObject(
                            {
                                "parameters": [
                                    oas.ParameterObject(
                                        {
                                            "name": "a",
                                            "in": "query",
                                            "schema": foo,
                                            "required": False,
                                        }
                                    )
                                ],
                                "responses": {
                                    "200": oas.ResponseObject(
                                        {
                                            "description": "OK",
                                            "content": {
                                                "application/json": oas.MediaTypeObject(
                                                    {"schema": bar}
                                                )
                                            },
                                        }
                                    )
                                },
                            }
                        )
                    }
                )
            },
        }
    )
) == {
    "openapi": "3.0.3",
    "info": {"title": "API Document", "version": "0.1.0"},
    "components": {"schemas": {"foo": {"type": "string"}}},
    "paths": {
        "/": {
            "get": {
                "parameters": [
                    {
                        "name": "a",
                        "in": "query",
                        "schema": {"$ref": "#/components/schemas/foo"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/foo"},
                                }
                            }
                        },
                    }
                },
            }
        }
    },
}
```

项目不提供结构、数据正确验证，可使用 [openapi-spec-validator](https://github.com/python-openapi/openapi-spec-validator) 进行验证。
