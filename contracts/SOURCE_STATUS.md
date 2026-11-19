# Contract source status and conformance gate

The common brief states contract v1.0.2 is final/frozen. The supplied ZIP's README and OpenAPI metadata still say DRAFT / 1.0.0-draft. Preserve this discrepancy for the team lead to resolve; do not silently relabel contract artefacts.

The original `events.schema.json`, `openapi.yaml`, sample event files and sample response files have not yet been copied from the supplied ZIP into this repository. The original ZIP remains the authority. The current backend enforces the main event envelope with Pydantic and exposes most contract routes, but it must not be described as full JSON-Schema/OpenAPI contract conformance until the exact files are restored and the implementation is checked against them.
