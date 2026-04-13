# Requirements Document: Command-Line Calculator

## 1. Purpose

Develop a simple command-line calculator program that accepts three positional
arguments representing a binary arithmetic expression, evaluates it, and prints
the result to stdout.

## 2. Scope

- A single self-contained Python script (or module) named `calc.py`.
- Supports the four basic arithmetic operations: addition, subtraction,
  multiplication, and division.
- Operates entirely from the command line; no interactive prompts, no GUI.

## 3. Functional Requirements

### 3.1 Command-Line Interface

The program is invoked with exactly three positional arguments:

```
python calc.py <left_operand> <operator> <right_operand>
```

| Position | Name           | Type   | Description                             |
|----------|----------------|--------|-----------------------------------------|
| 1        | left_operand   | number | The left-hand side of the expression.  |
| 2        | operator       | string | One of: `+`, `-`, `*`, `/`             |
| 3        | right_operand  | number | The right-hand side of the expression. |

Examples:

```
python calc.py 1 + 1     → 2
python calc.py 2 - 1     → 1
python calc.py 2 '*' 2   → 4
python calc.py 4 / 2     → 2.0
```

> Note: `*` may need to be quoted in some shells to prevent glob expansion.
> The program itself does not need to handle quoting — the shell passes the
> literal string to `sys.argv`.

### 3.2 Computation

- Parse `left_operand` and `right_operand` as floating-point numbers.
- Apply the arithmetic operator to produce the result.
- Supported operators and their semantics:
  - `+` — addition
  - `-` — subtraction
  - `*` — multiplication
  - `/` — true division (not integer division)

### 3.3 Output

- Print only the result to stdout, followed by a newline.
- If the result is a whole number (e.g., `2.0`), it **may** be displayed as an
  integer (`2`) — either representation is acceptable.

### 3.4 Error Handling

| Error condition               | Expected behaviour                                      |
|-------------------------------|---------------------------------------------------------|
| Wrong number of arguments     | Print a usage message to stderr; exit with code 2.     |
| Non-numeric operand(s)        | Print an error message to stderr; exit with code 1.    |
| Unsupported operator          | Print an error message to stderr; exit with code 1.    |
| Division by zero              | Print `"Error: division by zero"` to stderr; exit 1.  |

## 4. Non-Functional Requirements

- **No external dependencies** — use the Python standard library only.
- **Single file** — the entire implementation lives in `calc.py`.
- **Readable code** — use meaningful variable names; add a brief docstring or
  inline comments where the logic is not immediately obvious.
- **Exit codes** — follow Unix conventions: `0` for success, `1` for runtime
  errors, `2` for usage errors.

## 5. Acceptance Criteria

1. `python calc.py 1 + 1` prints `2` (or `2.0`) and exits 0.
2. `python calc.py 2 - 1` prints `1` (or `1.0`) and exits 0.
3. `python calc.py 2 '*' 2` prints `4` (or `4.0`) and exits 0.
4. `python calc.py 4 / 2` prints `2.0` (or `2`) and exits 0.
5. `python calc.py 1 % 1` exits 1 with an error message on stderr.
6. `python calc.py 1 / 0` exits 1 with `"Error: division by zero"` on stderr.
7. `python calc.py 1 + abc` exits 1 with an error message on stderr.
8. `python calc.py 1 +` exits 2 with a usage message on stderr.

---
*End of Requirements Document*
