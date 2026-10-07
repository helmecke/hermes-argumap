"""Native Hermes registration for local Argumap operations."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .schemas import ARGUMAP_OPERATION


def _adapter():
    # Environment settings keep mutable files explicit and outside curated content.
    from argumap import CaseRepository, CaseService, HermesAdapter

    metadata_root = Path(os.environ.get("ARGUMAP_METADATA_ROOT", ".argumap/metadata"))
    export_root = Path(os.environ.get("ARGUMAP_EXPORT_ROOT", ".argumap/exports"))
    repository = CaseRepository.from_metadata_root(metadata_root)
    return HermesAdapter(repository, CaseService(repository, export_root))


def argumap_operation(arguments: dict[str, Any], **_: Any) -> str:
    """Return all domain failures as structured JSON for the Hermes runtime."""
    try:
        if not isinstance(arguments, dict):
            return json.dumps({"ok": False, "error": {"field": "arguments", "message": "must be an object"}})
        operation, payload = arguments.get("operation"), arguments.get("payload")
        if not isinstance(operation, str) or not isinstance(payload, dict):
            return json.dumps({"ok": False, "error": {"field": "arguments", "message": "operation must be a string and payload must be an object"}})
        return json.dumps(_adapter().invoke(operation, payload))
    except Exception as error:  # Tool handlers must not propagate into Hermes.
        return json.dumps({"ok": False, "error": {"field": "runtime", "message": str(error)}})


def register(ctx: Any) -> None:
    """Register the documented native-plugin tool surface."""
    ctx.register_tool(name="argumap_operation", toolset="argumap", schema=ARGUMAP_OPERATION, handler=argumap_operation)
