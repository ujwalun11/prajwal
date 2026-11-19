# Contract source notice

The authoritative source supplied to this project is the uploaded `contracts_v1_draft.zip` bundle, containing `events.schema.json`, `openapi.yaml`, `DECISIONS.md`, sample events and sample responses.

**Important source-status discrepancy:** the common brief identifies contract v1.0.2 as final/frozen, while the uploaded contracts README and OpenAPI metadata still label the contract DRAFT / 1.0.0-draft. The team should resolve this status label explicitly. Implementations must preserve the supplied payloads and endpoint semantics meanwhile.

The uploaded bundles are provided to the repository maintainer separately. Do not invent or silently revise a contract file. The implementation uses the exact event type names, envelope fields, API routes and decisions captured in the supplied source bundle.
