"""
export_api_docs.py

Sprint 6
Day 40

Exports the FastAPI OpenAPI schema to docs/openapi.json and
converts it into a minimal Postman collection at
docs/postman_collection.json.
"""

import json
import os

from src.api.main import app

OPENAPI_OUTPUT_FILE = "docs/openapi.json"
POSTMAN_OUTPUT_FILE = "docs/postman_collection.json"

BASE_URL = "http://localhost:8000"


def export_openapi_schema() -> dict:
    """
    Write the app's OpenAPI schema to docs/openapi.json.

    Returns:
        The OpenAPI schema dict.
    """

    schema = app.openapi()

    os.makedirs(os.path.dirname(OPENAPI_OUTPUT_FILE), exist_ok=True)

    with open(OPENAPI_OUTPUT_FILE, "w") as f:
        json.dump(schema, f, indent=2)

    print(f"✔ OpenAPI schema saved : {OPENAPI_OUTPUT_FILE}")

    return schema


def build_postman_collection(schema: dict) -> dict:
    """
    Convert an OpenAPI schema into a minimal Postman v2.1
    collection, grouping requests by tag.

    Args:
        schema: The OpenAPI schema dict.

    Returns:
        A Postman collection dict.
    """

    folders: dict = {}

    for path, methods in schema["paths"].items():
        for http_method, operation in methods.items():

            tag = (operation.get("tags") or ["Untagged"])[0]
            folders.setdefault(tag, [])

            folders[tag].append(
                {
                    "name": operation.get("summary") or f"{http_method.upper()} {path}",
                    "request": {
                        "method": http_method.upper(),
                        "header": [],
                        "url": {
                            "raw": f"{BASE_URL}{path}",
                            "host": [BASE_URL],
                            "path": path.strip("/").split("/"),
                        },
                    },
                }
            )

    collection = {
        "info": {
            "name": "N100 Financial Platform API",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": [{"name": tag, "item": requests} for tag, requests in folders.items()],
    }

    return collection


def export_postman_collection(schema: dict) -> None:
    """
    Write the Postman collection to docs/postman_collection.json.

    Args:
        schema: The OpenAPI schema dict.
    """

    collection = build_postman_collection(schema)

    os.makedirs(os.path.dirname(POSTMAN_OUTPUT_FILE), exist_ok=True)

    with open(POSTMAN_OUTPUT_FILE, "w") as f:
        json.dump(collection, f, indent=2)

    print(f"✔ Postman collection saved : {POSTMAN_OUTPUT_FILE}")


def main() -> None:
    """
    Export both the OpenAPI schema and the Postman collection.
    """

    schema = export_openapi_schema()
    export_postman_collection(schema)


if __name__ == "__main__":
    main()
