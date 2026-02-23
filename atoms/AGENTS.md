# Atoms Module Documentation

## Overview

The Atoms module contains atomic service definitions and implementations that form the building blocks of business flows. Each atom represents a specific, reusable capability that can be composed into larger workflows.

## Structure

### Atom Definition Format

Atoms are defined in JSON files with the following structure:

```json
{
  "id": "string (unique atom identifier, e.g. 'package.service.function')",
  "category": "string (logical grouping)",
  "description": "string (purpose and behavior)",
  "inputs": [
    {
      "name": "string (input parameter name)",
      "type": "string (data type)",
      "required": "boolean (whether this input is mandatory)",
      "description": "string (details about the input)"
    }
  ],
  "outputs": [
    {
      "name": "string (output parameter name)",
      "type": "string (data type)",
      "description": "string (details about the output)"
    }
  ],
  "constraints": {
    "preconditions": "string[] (requirements before execution)",
    "postconditions": "string[] (guarantees after execution)"
  }
}
```

### Current Atom Packages

#### 1. Common Atoms (`atoms/common.json`)
- **`common.file.get_file_size`**: Get the size of a file from its path

#### 2. GlobalX Atoms (`atoms/globalx.json`)
- **`globalx.permission.grant_permission`**: Grant permission for file transfer
- **`globalx.permission.query_permissions`**: Check user's permissions
- **`globalx.space.query_quota`**: Query user's storage quota
- **`globalx.transfer.file_transfer`**: Transfer a file between users

## Implementation Structure

### Python Implementations

Each atom package has corresponding Python implementations in subdirectories:

- `atoms/common/file.py` - Implementation for common file operations
- `atoms/globalx/permission.py` - Implementation for permission operations
- `atoms/globalx/space.py` - Implementation for space/quota operations
- `atoms/globalx/transfer.py` - Implementation for file transfer operations

### Shared Context Mechanism

Atoms can share data through a context mechanism:

- Each step's outputs become available in the shared context
- Later steps can reference previous outputs using `${step_id.outputs.output_name}` syntax
- The planner generates plans with proper dependency ordering based on these references

## Executor Mapping Contract (for upcoming executor)

To avoid ambiguity when executor is implemented, keep this mapping contract:

1. Atom ID naming convention:
   - `package.domain.action` (example: `globalx.permission.query_permissions`)
2. Python callable mapping convention:
   - Module path: `atoms/<package>/<domain>.py`
   - Function name: `<action>`
   - Example: `globalx.permission.query_permissions` -> `atoms/globalx/permission.py::query_permissions`
3. Function signature convention:
   - Parameters should match atom input names in `*.json`
   - Return value should align with declared outputs:
     - one output: scalar return value
     - multiple outputs: dict/object keyed by output names
     - no outputs: return `None`
4. If mapping cannot be resolved at runtime, executor should fail the step with a structured error indicating unresolved atom implementation.

## Loading Process

### Atoms Registry

1. **Discovery:** System scans `atoms/*.json` for atom definition files
2. **Loading:** Each JSON file is parsed and atoms are extracted from the `atoms` array (files that fail to parse are silently skipped)
3. **Registration:** Atoms are registered with unique IDs (`atom.id`) in the registry
4. **Caching:** Registry caching is currently handled by API layer process cache (not by the loader function itself)

## Reference Resolution

### Input References

Steps can reference outputs from previous steps:

```
${step_id.outputs.output_name}
```

Where:
- `step_id` is the identifier of a previous step (explicitly set or auto-generated from index)
- `outputs` is the outputs section of the referenced step
- `output_name` is the specific output field to reference

### Dependency Management

The system maintains dependencies based on references:
- Explicit dependencies defined in `depends_on` field
- Implicit dependencies created by input references
- Topological sorting to determine execution order
- Cycle detection to prevent circular dependencies

## Validation Integration

### Schema Compliance

- All atom definitions must conform to the expected JSON structure
- Required fields are validated during loading
- Input/output specifications must match the defined schema

### Runtime Validation

- Plan validator ensures step IDs exist in the registry
- Input parameters match atom specifications
- Required inputs are provided for each atom
- Output references point to valid previous steps

## Extensibility

### Adding New Atoms

To add new atoms to the system:

1. Define the atom in the appropriate JSON file (or create a new one)
2. Implement the functionality in the corresponding Python file
3. Ensure the function signature matches the atom definition and mapping contract above
4. Update documentation if necessary

### Best Practices

- Keep atoms focused on single responsibilities
- Provide clear, descriptive names and documentation
- Define precise input and output schemas
- Consider error handling and edge cases in implementations
