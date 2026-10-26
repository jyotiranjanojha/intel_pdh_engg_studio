# PDH Engineering Studio

Streamlit in Snowflake app for the PDH data engineering lifecycle. It turns accepted Rule Repository rules (or an FDD Excel file) into validated, PDH-standard Snowflake code, then tracks that code from development to lead verification.

See also: [PRD.md](PRD.md) (what and why) · [ARCHITECTURE.md](ARCHITECTURE.md) (how it's built).

## Pages

| Section | Page | What it does |
|---|---|---|
| — | Home | Live metrics and module overview |
| Development | Code Generator | Generate views, ROOT tables + Maintain procedures and Time Travel bundles from the Rule Repository, FDD Excel or existing code; validated against Snowflake |
| Development | Compliance Analyzer | FDD validation, naming and standards compliance |
| Analysis | Change Impact Analyzer | Impact of a column / object / metadata change across lineage |
| Analysis | Data Journey Explorer | Trace an item through every pipeline layer and find where it drops |
| Quality Engineering | TDD Generator | Technical Design Document from requirements or FDD |
| Quality Engineering | Unit Test Generator | SQL test suite per object; export or run in-app |
| Pipeline Intelligence | Pipeline Flow | Module lineage diagram with live row counts |
| Pipeline Intelligence | Rule Drift Monitor | Flags deployed code that is stale against current rules |
| Pipeline Intelligence | Dev Completion Tracker | Module hand-off with the Rule Repository; Dev Completed → lead Verify / Reject |
| Intelligence | AI Engineering Assistant | Natural-language questions on rules and pipeline objects |
| Future Enhancements | Code Reviewer | AI-assisted code review with lead approval |

## Project structure

```
pdh-command-center/
├── streamlit_app.py          # entry point: page config, CSS, navigation, shared connection
├── snowflake.yml             # Streamlit object definition + deployed artifacts list
├── pyproject.toml            # Python dependencies
├── .streamlit/config.toml    # theme
├── app_pages/                # one file per page
│   ├── home.py
│   ├── code_generator.py
│   ├── compliance_analyzer.py
│   ├── impact_simulator.py   # Change Impact Analyzer
│   ├── item_tracer.py        # Data Journey Explorer
│   ├── tdd_generator.py
│   ├── unit_test_generator.py
│   ├── object_flow.py        # Pipeline Flow
│   ├── drift_monitor.py
│   ├── dev_tracker.py
│   ├── cortex_analyst.py     # AI Engineering Assistant
│   └── code_reviewer.py
├── utils/
│   ├── config.py             # environment settings — change only this when moving accounts
│   ├── codegen_pipeline.py   # route → context → design → generate → validate → wrap → save
│   ├── lineage_parser.py
│   ├── impact_analyzer.py
│   ├── discovery.py
│   ├── module_config.py      # Data Journey Explorer stages per module
│   ├── ai_helpers.py         # cached Cortex calls
│   └── rule_repo_health.py   # Rule Repository schema check
├── ddl/                      # app-owned T_CMD_* table DDL
└── dbt_macros/               # pattern templates
```

## Prerequisites

| Item | Value |
|---|---|
| Database | `IF_SUPPLY_CHAIN` |
| App role (sharing) | `ROLE_IF_CDA_PDH_SUPPLY_PLANNING_ANALYSIS_CONTRIBUTOR` |
| Warehouse | `IF_WH_SCHAIN_IFPDH_CONSUMPTION` |
| Compute pool | `SYSTEM_COMPUTE_POOL_CPU` (Container Runtime) |
| Cortex | Access to `SNOWFLAKE.CORTEX.COMPLETE` with claude-opus-4-5, claude-sonnet-4-5, claude-haiku-4-5 |
| App tables | `T_CMD_*` in `PDH_SUPPLY_PLANNING_XFRM_BASE` (see `ddl/`) |
| Rule Repository | `VW_RULE_SUMMARY`, `VW_MODULE_DEV_STATUS`, `VW_MODULE_DEV_OBJECTS`, `VW_RULE_CHANGES_FOR_DEV`, `SP_SET_MODULE_DEV_STATUS` |

To run in another account or environment, update `utils/config.py` (database, schemas, warehouse, role) and the `identifier` / `query_warehouse` in `snowflake.yml`.

## Deploy

1. Open the project in Snowsight Workspaces.
2. Make sure **every file you added or changed is listed under `artifacts:` in `snowflake.yml`**. Only listed files are deployed.
3. Click **Deploy**.
4. If a change to a `utils/` module doesn't show up, reboot the app (⋮ → Reboot). Streamlit keeps imported modules in memory. The Code Generator reloads `codegen_pipeline` automatically when the file changes; other modules need a reboot.

## Adding a page

1. Create `app_pages/<name>.py`. Start with `conn = st.session_state["conn"]`.
2. Register it in `st.navigation` in `streamlit_app.py`, under the right section.
3. Add it to the matching card in `app_pages/home.py`.
4. Add the file to `artifacts:` in `snowflake.yml`.

## Conventions

- **Reads:** `conn.query(sql, ttl=…)`. Wrap reusable lookups in `@st.cache_data(show_spinner=False)` with a `_conn` argument.
- **Writes:** `from snowflake.snowpark.context import get_active_session; get_active_session().sql(q).collect()`.
- **Escaping:** every value goes through `sqval()` (escape `\` and `'`). Never format raw user input into SQL.
- **Cortex:** `SNOWFLAKE.CORTEX.COMPLETE('<model>', [{'role':'user','content': $$…$$}], {'max_tokens': N, 'temperature': 0})`; read `choices[0].messages`.
- **Generated code follows PDH standards:**
  - `USE ROLE`, then `USE SCHEMA`;
  - column list in the CREATE header, and the comment header after `AS`;
  - fully qualified names everywhere;
  - leading commas and tab indentation;
  - no `SELECT *` and no `ORDER BY` in views;
  - metadata values read from `V_CRR_BUSINESS_RULE_METADATA_DETAIL_CORE_PIT`, never hardcoded.
- **File header:** every file starts with a one-line purpose comment.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `unexpected keyword argument …` after a deploy | Stale module in memory, or the file is missing from `artifacts:` | Check `snowflake.yml`, redeploy, reboot the app |
| `KeyError: 'mode'` on the Code Generator | Result saved in session state by an older version | Regenerate (the page discards old results automatically) |
| "Could not save deployment record" | Write called outside the Snowflake session | Only happens outside the app (local tests). In the app, check grants on `T_CMD_CODE_DEPLOYMENT` |
| Module or target missing in the Code Generator | Module not `READY_FOR_DEV` / `IN_DEV`, or no `ACCEPTED` rules | Check the module in the Rule Repository |
| Metric shows `-` on Home | Query failed (object or column missing, or no access) | Run the metric query from `home.py` in a worksheet |
