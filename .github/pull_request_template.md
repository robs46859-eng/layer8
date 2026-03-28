## Summary

- Describe the user-visible or operational change
- Link any related issues or incidents

## Changes

- List the main code paths touched
- Call out schema, config, or deployment changes

## Validation

- [ ] `pytest tests`
- [ ] `ruff check .`
- [ ] `python -m compileall app scripts tests`
- [ ] Local smoke test completed if runtime behavior changed

## Risk

- Describe failure modes, rollback plan, and any follow-up work

## Checklist

- [ ] Tests added or updated where behavior changed
- [ ] Docs and env examples updated where needed
- [ ] Security-sensitive changes reviewed
- [ ] Deployment impact understood
