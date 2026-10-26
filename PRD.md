# PDH Engineering Studio — Product Requirements Document

| | |
|---|---|
| **Product** | PDH Engineering Studio (Streamlit app `PDH_COMMAND_CENTER`) |
| **Platform** | Streamlit in Snowflake, Container Runtime |
| **Data** | `IF_SUPPLY_CHAIN` (PDH Common + Supply Planning schemas) |
| **Owner** | Ishtiyaq Rahman |
| **Companion app** | Rule Repository / FDD Command Center (Priti Sharma) |
| **Version** | 4.0 |

---

## 1. Purpose

The Rule Repository captures **what** the PDH pipeline must do: business rules written by BAs and POs, reviewed and accepted per module.
PDH Engineering Studio covers **how** it gets built and kept correct. It turns accepted rules into Snowflake code that follows PDH standards, validates that code against live objects, tracks development until a lead verifies it, and shows when deployed code has drifted from the rules.

## 2. Goals

1. Generate PDH-standard Snowflake code (views, ROOT tables, Maintain procedures, Time Travel bundles) directly from accepted rules or an FDD Excel file.
2. Ground every generated object in real metadata — actual source columns, live DDL, business-rule metadata rows — and validate it by compiling against Snowflake before a developer sees it.
3. Give BAs, developers and leads one shared lifecycle per module: **Ready for Dev → In Dev → Dev Completed → Verified**.
4. Detect rule changes after code was generated, so stale code is caught before release.
5. Shorten analysis work: impact of a change, where an item drops in the pipeline, test cases, and design documents.

## 3. Personas

| Persona | Needs | Main pages |
|---|---|---|
| **BA / PO** | See whether their rules are implemented; trace an item through the pipeline | Dev Completion Tracker, Data Journey Explorer, Rule Drift Monitor |
| **Developer** | Generate correct, standard code fast; know exactly what changed in the rules | Code Generator, Unit Test Generator, TDD Generator, Change Impact Analyzer |
| **Lead / Verifier** | Verify completed objects against the live code; approve or reject | Dev Completion Tracker, Compliance Analyzer |
| **Governance** | Standards compliance, audit trail of generated and deployed code | Compliance Analyzer, Rule Drift Monitor |

## 4. Features

Status: **Live** = in production use · **Future** = in progress.

### 4.1 Development

#### Code Generator — Live
Generate Snowflake artifacts in three modes.

**From Rule Repository**
- Select **module → target object**. Only modules in `READY_FOR_DEV` / `IN_DEV` are offered for development, and the module state is shown per module.
- Each target is routed to the cheapest correct method:

  | Route | When | How |
  |---|---|---|
  | PIT view | `V_*_PIT` with a matching `F_*` table function | Standard `p_crr_timetravel_pit_base_view_builder` template, no AI |
  | 1:1 view | No logic, single source | Deterministic pass-through |
  | Transformation | Everything else | AI pipeline: analyse → design → generate → validate |

- **AI pipeline:**
  1. Build grounded context: column spec, real source columns, ROOT-view mapping, metadata rows ranked by relevance, live DDL, table-function signatures, and reference DDLs from the pattern library.
  2. Design the CTE plan with claude-opus-4-5.
  3. Generate the SELECT body only.
  4. Compile it, count rows, match columns, run standards lint, and do one repair pass.
  5. Check rule coverage with claude-sonnet-4-5.
  6. Wrap it deterministically with CREATE, header, `USE ROLE` / `USE SCHEMA` and tab formatting.
- Blockers (real open business questions) stop generation and are shown to the developer. **Developer notes** let the developer resolve them and regenerate.
- **Tables:** a ROOT table plus its Maintain procedure, with the load pattern chosen per object:
  - **MERGE**: IUD flag, soft delete via `DELETE_IND`, reactivation, null-safe diff.
  - **TRUNCATE & LOAD**.
  - Both include a source duplicate check (`duplicate_records_from_source`, -20100), separate exception handlers and activity logging.
- **Time Travel bundle:** CORE_CURRENT, CORE_MEMORIES, the TimeTravel procedure, the PIT function and the PIT view, generated without AI.
- Every generation is recorded in `T_CMD_CODE_DEPLOYMENT` with a rule snapshot, a hash and validation results.

**From FDD Excel**
- Parses the FDD workbook into an object chain: SRC_BASE, SRC, XFRM_BASE, XFRM, ANALYSIS, TIMETRAVEL, METADATA.
- Deterministic objects use templates.
- Transformation views go through the same AI pipeline as Rule Repository mode, using the FDD's own column list and transformation blocks.
- Combined download in deployment order. Unvalidated objects are clearly marked.

**Update existing code**
- Fetch the live DDL of an object and apply a described change while keeping PDH standards.

#### Compliance Analyzer — Live
- FDD validation plus naming and coding-standards compliance (PDH / Intel standards) for objects and generated code.

### 4.2 Analysis

#### Change Impact Analyzer — Live
- Multi-mode impact analysis (column, object, metadata rule) across lineage (`T_CMD_LINEAGE`) and the pattern library.
- History is kept in `T_CMD_IMPACT_HISTORY`.

#### Data Journey Explorer — Live
- Trace an item ID through every pipeline layer: source → ROOT → STAGE → CORE_CURRENT / MEMORIES → PIT → HYBRID / UPI → Supply Planning consumers.
- Shows where it truly **drops** versus temporary **gaps**, checks metadata inclusion rules, and gives an AI root-cause diagnosis.

### 4.3 Quality Engineering

#### TDD Generator — Live
- Technical Design Documents from requirements or an FDD Excel upload, using pipeline metadata and patterns.

#### Unit Test Generator — Live
- A full SQL test suite per object from the Rule Repository and INFORMATION_SCHEMA.
- Covers row counts, keys, nulls, duplicates, rule conditions and referential checks.
- Export as SQL or CSV, or run all tests in the app.

### 4.4 Pipeline Intelligence

#### Pipeline Flow — Live
- Lineage diagram per module with live row counts.

#### Rule Drift Monitor — Live
- Compares rules accepted after a deployment with the rules snapshot stored at generation time.
- Flags objects whose code is stale, distinguishing logic changes from wording changes.

#### Dev Completion Tracker — Live
- **Module Development tab:**
  - module state from the Rule Repository;
  - per-object code status;
  - the **live Snowflake DDL** of each object (what is actually deployed);
  - rule changes since the code was generated.
- **Developer action:** "Mark as Dev Completed", per object and per module. Module state is set through `SP_SET_MODULE_DEV_STATUS`.
- **Lead action:** Verify or Reject with notes. Status is synced to `T_CMD_CODE_DEPLOYMENT` and `T_CMD_DEV_VERIFICATION`.
- **Verification History tab:** the full audit trail.

### 4.5 Intelligence

#### AI Engineering Assistant — Live
- Natural-language questions on rule tables and pipeline objects: SQL generation, explanations, root-cause analysis.

### 4.6 Future Enhancements

#### Code Reviewer — Future
- AI-assisted code review with lead approval (`T_CMD_REVIEW_REQUEST`, `T_CMD_REVIEW_COMMENT`).

## 5. Rule Repository integration contract

The two apps share data only through these objects. Neither app writes to the other's tables directly.

| Object | Owner | Used by Studio for |
|---|---|---|
| `PDH_SUPPLY_PLANNING_XFRM.VW_RULE_SUMMARY` | Rule Repository | Accepted rules per target object |
| `PDH_SUPPLY_PLANNING_XFRM.VW_MODULE_DEV_STATUS` | Rule Repository | Module state, rule / object counts, last decision |
| `PDH_SUPPLY_PLANNING_XFRM.VW_MODULE_DEV_OBJECTS` | Rule Repository | Objects per module with code / review / dev status |
| `PDH_SUPPLY_PLANNING_XFRM.VW_RULE_CHANGES_FOR_DEV` | Rule Repository | Rule changes (LOGIC / WORDING) since a timestamp |
| `PDH_SUPPLY_PLANNING_XFRM_BASE.SP_SET_MODULE_DEV_STATUS(module_id, state, note, user, app)` | Rule Repository | Set `DEV_COMPLETED` / `REOPENED` |
| `PDH_SUPPLY_PLANNING_XFRM_BASE.T_CMD_CODE_DEPLOYMENT` | Studio | Generated SQL, rule snapshot, status, deployed timestamp |
| `PDH_SUPPLY_PLANNING_XFRM_BASE.T_CMD_DEV_VERIFICATION` | Studio | Dev completion and lead verification records |

### Lifecycle

```
Rule Repository:  DRAFT → IN_REVIEW → ACCEPTED → module READY_FOR_DEV
Studio:           GENERATED → DEV_COMPLETED → VERIFIED
                                          ↘ REJECTED → (regenerate) → GENERATED
Module:           READY_FOR_DEV → IN_DEV → DEV_COMPLETED  (REOPENED on new logic changes)
```

## 6. Non-functional requirements

| Area | Requirement |
|---|---|
| Runtime | Streamlit in Snowflake, Container Runtime (`SYSTEM_COMPUTE_POOL_CPU`), owner's rights |
| Warehouse | `IF_WH_SCHAIN_IFPDH_CONSUMPTION` |
| AI | Snowflake Cortex `COMPLETE`: claude-opus-4-5 (design / generation), claude-sonnet-4-5 (coverage review, analysis), claude-haiku-4-5 (short summaries) |
| Data writes | Only to app-owned `T_CMD_*` tables, through the Snowpark session with escaped literals |
| Generated code | PDH standards: `USE ROLE` / `USE SCHEMA`, column list in the CREATE header, comment block after `AS`, fully qualified names, leading commas, tabs, no `SELECT *`, metadata values read from the metadata view rather than hardcoded |
| Auditability | Every generation stored with a rule snapshot, a hash, models used, the design, validation and coverage |

## 7. Success metrics

| Metric | Definition |
|---|---|
| First-pass validation rate | % of generated objects that compile and match the column spec without a manual edit |
| Rule-to-deploy lead time | Time from module `READY_FOR_DEV` to all objects `VERIFIED` |
| Drift caught before release | Stale objects flagged by the Drift Monitor before deployment |
| Verification turnaround | Time from `DEV_COMPLETED` to lead decision |
