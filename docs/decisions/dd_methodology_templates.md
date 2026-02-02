# Design Decision: Methodology Templates for Relationship Scaffolding

**Date:** 2025-02-01
**Status:** Proposed
**Context:** Bootstrap scan and artifact discovery

## Decision

The trace system will support **methodology templates** - predefined artifact types and relationship chains based on standard engineering practices.

## Rationale

1. **Bootstrap problem**: New projects or pre-existing repos need structure. Without guidance, artifact registration is ad-hoc.

2. **Standard patterns exist**: Engineering methodologies define expected artifacts and their relationships:
   - Systems Engineering (V-model): ConOps → SRS → Architecture → Design → Code → Test
   - DoDAF: OV-1 → SV-1 → SV-4 → Implementation  
   - Agile: Epic → Story → Task → Code → Test
   - Lightweight: Decision → Code → Test

3. **Consistency**: Templates ensure projects follow recognizable patterns, making onboarding and auditing easier.

4. **AI guidance**: When CC has a template, it knows what artifacts to create and how to link them. Bootstrap scan becomes "apply template, then fill in actual files."

## Implementation Sketch

```yaml
# .trace/templates/systems-engineering.yaml
name: Systems Engineering (V-Model)
artifact_types:
  - conops
  - requirement  
  - architecture
  - design
  - code
  - unit_test
  - integration_test
  - system_test

relationship_chains:
  - [conops, requirement, derives_from]
  - [requirement, architecture, implements]
  - [architecture, design, implements]
  - [design, code, implements]
  - [code, unit_test, verified_by]
  - [unit_test, integration_test, precedes]
  - [integration_test, system_test, precedes]
```

## Behavior

1. `init` or `apply_template` loads template into graph as scaffold
2. Artifacts created with matching types auto-link to scaffold
3. Bootstrap scan uses template to categorize discovered files
4. Templates are suggestions, not enforcement - non-matching artifacts allowed

## Scope

- MVP: No templates (manual artifact typing)
- v0.2: Template library, apply command, scaffold creation
- Future: Custom template authoring, template inheritance

## Alternatives Considered

1. **No templates**: Rely on skill file and manual tagging. Problem: inconsistent, no guidance for new projects.

2. **Strict enforcement**: Reject artifacts that don't fit template. Problem: too rigid, breaks real-world flexibility.

3. **AI inference only**: Let CC figure out relationships. Problem: inconsistent, no standard vocabulary.

## Decision

Implement methodology templates in v0.2. Templates provide scaffold and vocabulary; actual linking remains flexible.

## References

- Roadmap v0.2 section
- ccmem patterns (less structured but similar intent)
- DoDAF, TOGAF, V-Model literature
