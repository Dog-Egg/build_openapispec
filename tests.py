import pytest

from build_openapispec import openapispec


@pytest.fixture
def oas():

    oas = openapispec("3.0.3")
    old_build = oas.build

    def new_build(*args, **kwargs):
        import json

        from openapi_spec_validator import validate

        result = old_build(*args, **kwargs)

        validate(result)  # check valid schema
        json.dumps(result)  # check json serializable

        return result

    oas.build = new_build
    return oas


def test_basic_build(oas):
    foo = oas.SchemaObject(
        {
            "type": "string",
        },
        key="foo",
    )

    result = oas.build(
        oas.OpenAPIObject(
            {
                "info": oas.InfoObject(
                    {
                        "title": "Test",
                        "version": "1.0.0",
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
                                                "name": "p1",
                                                "in": "query",
                                                "schema": foo,
                                            },
                                        ),
                                        oas.ParameterObject(
                                            {
                                                "name": "p2",
                                                "in": "query",
                                                "schema": foo,
                                            },
                                        ),
                                    ],
                                    "security": [
                                        oas.SecurityRequirementObject(
                                            scheme=oas.SecuritySchemeObject(
                                                {"type": "http", "scheme": "basic"},
                                                key="HTTPBasic",
                                            )
                                        )
                                    ],
                                    "deprecated": False,
                                    "responses": {
                                        "200": oas.ResponseObject(
                                            {
                                                "description": """
                                                                # TITLE

                                                                ## DESCRIPTION
                                                                """,
                                                "content": {
                                                    "application/json": oas.MediaTypeObject(
                                                        {
                                                            "schema": oas.SchemaObject(
                                                                {
                                                                    "type": "object",
                                                                    "properties": {
                                                                        "foo": oas.SchemaObject(
                                                                            {
                                                                                "type": "string",
                                                                                "pattern": oas.non_empty(
                                                                                    None
                                                                                ),
                                                                                "maxLength": oas.non_empty(
                                                                                    10
                                                                                ),
                                                                            },
                                                                        )
                                                                    },
                                                                }
                                                            )
                                                        }
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
    )
    assert result == {
        "openapi": "3.0.3",
        "info": {
            "title": "Test",
            "version": "1.0.0",
        },
        "paths": {
            "/": {
                "get": {
                    "parameters": [
                        {
                            "in": "query",
                            "name": "p1",
                            "schema": {
                                "$ref": "#/components/schemas/foo",
                            },
                        },
                        {
                            "in": "query",
                            "name": "p2",
                            "schema": {
                                "$ref": "#/components/schemas/foo",
                            },
                        },
                    ],
                    "security": [
                        {
                            "HTTPBasic": [],
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "# TITLE\n\n## DESCRIPTION",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "foo": {"type": "string", "maxLength": 10},
                                        },
                                    }
                                }
                            },
                        },
                    },
                },
            },
        },
        "components": {
            "schemas": {
                "foo": {
                    "type": "string",
                },
            },
            "securitySchemes": {
                "HTTPBasic": {
                    "scheme": "basic",
                    "type": "http",
                },
            },
        },
    }


def test_refs_1(oas):
    """
    测试一种嵌套引用的例子
    """
    foo = oas.SchemaObject(
        {"type": "string"},
        key="foo",
    )
    bar = oas.SchemaObject(
        {
            "type": "array",
            "items": foo,
        },
        key="bar",
    )

    # test 1
    assert oas.build(
        oas.OpenAPIObject(
            {
                "info": oas.InfoObject({"title": "title", "version": "1.0"}),
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
                                            }
                                        ),
                                        oas.ParameterObject(
                                            {
                                                "name": "b",
                                                "in": "query",
                                                "schema": bar,
                                            }
                                        ),
                                    ],
                                    "responses": {
                                        "200": oas.ResponseObject(
                                            {
                                                "description": "description",
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
                        },
                    )
                },
            }
        )
    ) == {
        "components": {
            "schemas": {
                "bar": {"type": "array", "items": {"$ref": "#/components/schemas/foo"}},
                "foo": {"type": "string"},
            },
        },
        "info": {
            "title": "title",
            "version": "1.0",
        },
        "openapi": "3.0.3",
        "paths": {
            "/": {
                "get": {
                    "parameters": [
                        {
                            "in": "query",
                            "name": "a",
                            "schema": {
                                "$ref": "#/components/schemas/foo",
                            },
                        },
                        {
                            "in": "query",
                            "name": "b",
                            "schema": {
                                "$ref": "#/components/schemas/bar",
                            },
                        },
                    ],
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/bar",
                                    },
                                },
                            },
                            "description": "description",
                        },
                    },
                },
            },
        },
    }

    # test 2
    assert oas.build(
        oas.OpenAPIObject(
            {
                "info": oas.InfoObject({"title": "title", "version": "1.0"}),
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
                                                "schema": bar,
                                            }
                                        ),
                                    ],
                                    "responses": {
                                        "200": oas.ResponseObject(
                                            {
                                                "description": "description",
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
                        },
                    )
                },
            }
        )
    ) == {
        "components": {
            "schemas": {"bar": {"type": "array", "items": {"type": "string"}}},
        },
        "info": {
            "title": "title",
            "version": "1.0",
        },
        "openapi": "3.0.3",
        "paths": {
            "/": {
                "get": {
                    "parameters": [
                        {
                            "in": "query",
                            "name": "a",
                            "schema": {
                                "$ref": "#/components/schemas/bar",
                            },
                        },
                    ],
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/bar",
                                    },
                                },
                            },
                            "description": "description",
                        },
                    },
                },
            },
        },
    }
