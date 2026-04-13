# Requirements Document: CSV Data Pipeline & Report Generator

## 1. Purpose

Develop a command-line tool that reads a CSV file, performs configurable
aggregations (sum, mean, count, group-by), and outputs a formatted Markdown
or HTML report summarising the results.

## 2. Scope

- A single Python module `csv_report.py` plus a supporting `aggregations.py`
  for computation logic.
- Accepts any well-formed CSV file with a header row.
- Aggregation behaviour is driven by a YAML config file supplied at runtime.
- Output is either Markdown (`.md`) or HTML (`.html`), chosen via a CLI flag.

## 3. Functional Requirements

### 3.1 Command-Line Interface

```
python csv_report.py --input <file.csv> --config <agg.yaml> --output <report.md|report.html> [--format md|html]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--input` | yes | — | Path to the source CSV file |
| `--config` | yes | — | Path to the aggregation YAML config |
| `--output` | yes | — | Path for the generated report |
| `--format` | no | inferred from `--output` extension | `md` or `html` |

### 3.2 Aggregation Config (YAML)

The YAML config describes one or more aggregation blocks:

```yaml
aggregations:
  - name: "Total Sales by Region"
    group_by: region
    column: sales
    operations: [sum, mean, count]

  - name: "Average Age"
    column: age
    operations: [mean, min, max]
```

- `group_by` is optional; when omitted the operation applies to the entire column.
- `operations` is a list of one or more of: `sum`, `mean`, `min`, `max`, `count`.
- `name` becomes the section heading in the report.

### 3.3 Computation

- Parse the CSV with the standard library `csv` module.
- Cast numeric columns automatically; leave non-numeric columns as strings.
- For each aggregation block:
  - If `group_by` is specified, partition rows by the unique values in that
    column and apply each operation per partition.
  - Otherwise apply each operation across all rows of the target column.
- Produce a structured result object consumed by the report renderer.

### 3.4 Report Output

**Markdown format:**
- One `##` section per aggregation block (using `name` as heading).
- Results rendered as a Markdown table with columns: Group (if applicable),
  Operation, Value.

**HTML format:**
- A self-contained HTML file with embedded CSS (no external dependencies).
- One `<section>` per aggregation block with a `<table>` for results.
- Minimal but readable styling (alternating row colours, clear headings).

### 3.5 Error Handling

| Error condition | Expected behaviour |
|---|---|
| Input CSV not found | Print error to stderr; exit 1 |
| Config YAML not found | Print error to stderr; exit 1 |
| Malformed YAML config | Print error with line hint to stderr; exit 1 |
| Referenced column missing in CSV | Print error naming the column; exit 1 |
| Non-numeric column used in numeric operation | Print error; exit 1 |
| Wrong number of CLI arguments | Print usage to stderr; exit 2 |

## 4. Non-Functional Requirements

- **No external dependencies** — standard library only (`csv`, `json`,
  `statistics`, `argparse`, `pathlib`). A `yaml` dependency is allowed for
  config parsing (`PyYAML`).
- **Modular** — parsing, aggregation, and rendering are in separate functions
  or modules; `csv_report.py` is the entry point only.
- **Tested** — unit tests in `tests/test_csv_report.py` cover at least:
  group-by aggregation, global aggregation, missing column error, and both
  output formats.

## 5. Acceptance Criteria

1. Given a CSV with columns `region,sales` and a config requesting
   `sum` and `mean` grouped by `region`, the report contains one table row
   per unique region with correct values.
2. `--format html` produces a valid, self-contained HTML file viewable in a
   browser.
3. `--format md` produces a valid Markdown file with correct table syntax.
4. Referencing a non-existent column exits 1 with a clear error message.
5. All unit tests pass (`python -m pytest tests/test_csv_report.py`).
6. Running the tool end-to-end on the provided sample CSV produces a report
   that matches the expected output fixture.

---
*End of Requirements Document*
