# Implementation Plan: PANBA UX baseline — 4-click tasks and defaulted inputs

**Branch**: `002-panba-is-palo` | **Date**: 2025-09-09 | **Spec**: C:\Users\marti\Documents\playground\PANBA\specs\002-panba-is-palo\spec.md
**Input**: Feature specification from `C:\Users\marti\Documents\playground\PANBA\specs\002-panba-is-palo\spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, or `GEMINI.md` for Gemini CLI).
6. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
8. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Primary requirement: Ensure every core task can be initiated in four or fewer clicks and every text input has a sensible default. Additionally, persist user preferences and credentials to avoid repeated inputs and support defaulting.

Technical approach: Persist a user-scoped configuration in Windows user AppData using a verbose, developer-editable JSON file. Store non-sensitive preferences (last-used paths, toggles, default durations) as plain JSON. Protect credentials using Windows DPAPI (pywin32 win32crypt) and store them as encrypted base64 blobs within the same config. Use `platformdirs.user_config_dir('PANBA','NTTIndonesia')` to resolve the config path (e.g., `%LOCALAPPDATA%\PANBA\config.json`). Load on app start to pre-fill fields and minimize clicks; write on successful operations to keep defaults current.

## Technical Context
**Language/Version**: Python 3.12 (cpython-312 observed)  
**Primary Dependencies**: customtkinter, requests, pandas, matplotlib, tkcalendar, tksheet, python-dotenv, platformdirs, pywin32 (DPAPI)  
**Storage**: Filesystem config in `%LOCALAPPDATA%\PANBA\config.json` via `platformdirs`; credentials encrypted via Windows DPAPI  
**Testing**: NEEDS CLARIFICATION (project lacks tests; propose adding minimal config read/write tests with temporary dirs)
**Target Platform**: Windows desktop (packaged via PyInstaller/Nuitka)  
**Project Type**: Single desktop app  
**Performance Goals**: Config IO must be near-instant; no noticeable UI lag  
**Constraints**: Four-click rule; always default inputs; avoid breaking existing UI flows; no network for config IO  
**Scale/Scope**: Single-user local config; small JSON (<100 KB)

Existing code analysis (scanned 4 areas):
- Startup (`app.py`): Reads optional `.env` only; no preference persistence.
- Credentials (`view/accountncredentials.py`): Fields exist, populated from `env`; no save of last-used inputs.
- File handling (`helper/filehandler.py`): Manages dialogs/exports; no persisted default directories.
- APIs (`helper/api/*`): Network calls; no config storage. Conclusion: New config module is needed; integrate lightly into existing views to set defaults and save on success.

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 1 (app only)
- Using framework directly: Yes (customtkinter directly; add a tiny config helper only)
- Single data model: Yes (single JSON file with one schema; no extra DTOs)
- Avoiding patterns: Yes (no repositories/UoW)

**Architecture**:
- Feature packaged as a small helper module (config) inside app; no extra project.
- Libraries used: platformdirs (path resolution), pywin32 (DPAPI), json (serialization).
- CLI: N/A (desktop app)
- Docs: Quickstart.md provided under specs

**Testing (NON-NEGOTIABLE)**:
- Planned: Add minimal unit tests for config read/write/encrypt later; not enforced today.
- Contract: JSON Schema supplied for config file.
- Use real DPAPI on Windows in tests; skip on non-Windows.

**Observability**:
- Log config load/save errors to existing UI log terminal where available; include path/context.

**Versioning**:
- Add `config.version` field; migration handled by loader with defaults and write-back.

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: [DEFAULT to Option 1 unless Technical Context indicates web/mobile app]
Structure Decision: Option 1 (single project). Add `helper/config.py` module later for IO and encryption.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved (created at `C:\Users\marti\Documents\playground\PANBA\specs\002-panba-is-palo\research.md`)

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `/scripts/update-agent-context.sh [claude|gemini|copilot]` for your AI assistant
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, quickstart.md (created under `C:\Users\marti\Documents\playground\PANBA\specs\002-panba-is-palo\`)

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P] 
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Models before services before UI
- Mark [P] for parallel execution (independent files)

**Task Generation Focus (for this feature)**:
- Create `helper/config.py` with functions: get_config_path(), load_config(), save_config(), encrypt_secret(), decrypt_secret().
- Integrate into `app.py` to load config early and pass defaults to views.
- Integrate into `view/accountncredentials.py` to pre-fill fields and persist on successful login; add a "Remember me" toggle defaulted ON.
- Integrate into file dialogs to remember last directories (`FileHandler.initDir`, export dest dir).
- Add non-blocking writes and basic error messaging.

**Estimated Output**: 12-18 tasks in tasks.md (created by /tasks)

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
– [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*