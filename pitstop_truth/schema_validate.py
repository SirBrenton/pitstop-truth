from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import jsonschema


class SchemaValidationError(ValueError):
    pass


def load_schema(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8"))


def iter_jsonl(path: str | Path) -> Iterable[Tuple[int, Dict[str, Any]]]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as ex:
                raise SchemaValidationError(f"{p}:{i}: invalid JSON: {ex}") from ex
            if not isinstance(obj, dict):
                raise SchemaValidationError(f"{p}:{i}: event must be an object (got {type(obj).__name__})")
            yield i, obj


def validate_against_schema(obj: Dict[str, Any], *, schema: Dict[str, Any], line_no: int) -> None:
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(obj), key=lambda e: list(e.path))
    if errors:
        e = errors[0]
        loc = ".".join(str(x) for x in e.path) if e.path else "<root>"
        raise SchemaValidationError(f"Line {line_no}: schema violation at {loc}: {e.message}")


def validate_jsonl_against_schema(jsonl_path: str | Path, schema_path: str | Path) -> int:
    schema = load_schema(schema_path)
    n = 0
    jsonl_path = Path(jsonl_path)

    for line_no, obj in iter_jsonl(jsonl_path):
        n += 1
        validate_against_schema(obj, schema=schema, line_no=line_no)

    if n == 0:
        raise SchemaValidationError(f"{jsonl_path}: no events found (empty JSONL)")
    return n