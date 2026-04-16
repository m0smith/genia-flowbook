# Flowbook Error Model (Clarified)

## Error Structure

All errors are structured as follows:

```json
{
  "type": "error",                // always present
  "code": "ERROR_CODE",            // always present
  "message": "Human-readable message", // always present
  "location": {
    "step": "parsing" | "validation" | "execution", // always present
    "context": "Description"         // always present
  },
  "cell_id": "optional",           // present for cell errors, omitted for parse errors
  "details": { ... },               // optional, context-specific
  "timestamp": "optional"          // optional, may be omitted
}
```

- `type`, `code`, `message`, and `location` are **always present**.
- `cell_id` is present for cell-specific errors, omitted for global/parse errors.
- `details` and `timestamp` are optional and may be omitted.

## Example

```json
{
  "type": "error",
  "code": "MISSING_CELL_REFERENCE",
  "message": "Cell 'p1' references cell 'v2' which does not exist",
  "location": {
    "step": "validation",
    "context": "Reference resolution"
  },
  "cell_id": "p1",
  "details": {"referenced_cell": "v2"}
}
```

## Field Presence Table

| Field      | Always Present | Optional | Notes                                  |
|------------|:-------------:|:--------:|----------------------------------------|
| type       |      ✓        |          | Always "error"                         |
| code       |      ✓        |          | Machine-readable error code            |
| message    |      ✓        |          | Human-readable message                 |
| location   |      ✓        |          | step/context                           |
| cell_id    |               |    ✓     | Only for cell-specific errors          |
| details    |               |    ✓     | Context-specific, may be omitted       |
| timestamp  |               |    ✓     | May be omitted                         |

