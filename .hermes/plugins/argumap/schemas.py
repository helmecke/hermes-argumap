"""Model-facing schema for the Argumap Hermes plugin."""

ARGUMAP_OPERATION = {
    "name": "argumap_operation",
    "description": "Create or inspect a local argument-review case, mutate its typed graph, analyze a snapshot, create a snapshot-bound verdict, or export it. Use only supported operation names and provide a payload matching that operation.",
    "parameters": {
        "type": "object",
        "additionalProperties": False,
        "required": ["operation", "payload"],
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["create_case", "get_case", "add_node", "add_relation", "analyze_case", "create_verdict", "export_snapshot"],
            },
            "payload": {"type": "object", "description": "Operation fields, including case_id for all operations except create_case."},
        },
    },
}
