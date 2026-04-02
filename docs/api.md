# API Reference

## Endpoint documentation standards

- Include HTTP method, route path, and authentication requirements for every endpoint.
- Define request schema (parameters, headers, body) using OpenAPI/Swagger conventions.
- Define response schema with status codes, body shape, and error contract.
- Document rate limits, pagination behavior, and idempotency guarantees where applicable.
- Link to source ownership and relevant [architecture decisions](./architecture.md).
- Provide `curl` or SDK examples for each endpoint to support quick integration.

## Endpoint template

### `METHOD /path`

- **Purpose:**
- **Auth:**
- **Inputs:**
- **Outputs:**
- **Failure modes:**
