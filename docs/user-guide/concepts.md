# Core Concepts

## Artifacts

An artifact is anything worth tracing: requirements, code, tests, decisions, documents.

**Types:**
| Type | Description | Example |
|------|-------------|---------|
| `requirement` | What the system should do | `REQ-AUTH-001` |
| `decision` | Design choices with rationale | `DD-001-use-networkx` |
| `module` | Code files | `src/auth/login.py` |
| `function` | Functions/methods (v0.5) | `src/auth/login.py::validate` |
| `test` | Test cases | `tests/test_auth.py` |
| `document` | Documentation | `docs/architecture.md` |
| `issue` | Bugs/tasks | `ISSUE-42` |

**Properties:**
- `artifact_id` - Unique identifier (often file path)
- `artifact_type` - One of the types above
- `file_path` - Where it lives in the repo
- `tags` - For discovery (`["auth", "security"]`)
- `content_hash` - For drift detection (v0.5)

## Relationships

Links connect artifacts with typed, directional edges.

**Types:**
| Relationship | Meaning | Example |
|--------------|---------|---------|
| `implements` | Code fulfills requirement | module → requirement |
| `depends_on` | A needs B to work | module → module |
| `verifies` | Test validates artifact | test → module |
| `supersedes` | New replaces old | decision → decision |
| `contains` | Parent has child | module → function |
| `references` | Generic link | document → decision |
| `derives_from` | Derived from source | requirement → requirement |

## Authority Model

All AI-generated content starts as **proposed**. Humans promote to **authoritative**.

```
[AI writes] → PROPOSED → [Human approves] → AUTHORITATIVE
```

**Why?**
- Prevents AI from creating false relationships
- Keeps humans in the loop
- Allows batch review

**Approval tools:**
- `accept_proposal(source, target)` - Single link
- `accept_all_proposed()` - Everything pending
- `accept_by_type("implements")` - All of one type
- `accept_by_source("auth_module")` - All from one artifact

## The Graph

Artifacts are nodes. Relationships are edges. Stored as NetworkX graph, rebuilt from event log.

```
[Requirement] ←implements← [Module] ←verifies← [Test]
      ↑                        ↓
      └────references──── [Decision]
```

**Query patterns:**
- `trace(artifact)` - Immediate neighbors
- `impact(artifact)` - Transitive downstream (what breaks?)
- `orphans()` - Disconnected artifacts

## Event Log

All changes recorded in `.trace/events.jsonl`:

```json
{"event_type": "artifact_added", "payload": {"artifact_id": "auth.py", ...}, "actor": "ai:claude-code", "state": "proposed"}
{"event_type": "link_added", "payload": {"source_id": "auth.py", "target_id": "REQ-1", ...}, "state": "proposed"}
{"event_type": "link_promoted", "payload": {"source_id": "auth.py", "target_id": "REQ-1"}, "actor": "human", "state": "authoritative"}
```

**Properties:**
- Append-only (never edited)
- Human-readable
- Git-diffable
- Source of truth (graph rebuilt from it)

## Methodology Templates

Pre-defined relationship patterns for common workflows:

- **systems-engineering** - Requirements → Design → Implementation → Test
- **agile** - Stories → Tasks → Code → Tests
- **lightweight** - Minimal: just code and tests

Templates help bootstrap expected relationships: "If you have requirements and modules, you probably need `implements` links."
