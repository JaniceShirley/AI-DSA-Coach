# Code Execution Architecture & Security Sandbox

## 1. Overview
The AI DSA Coach platform allows users to write and execute code against problem test cases. Security and isolation are primary architectural requirements: **arbitrary student code is NEVER executed directly within the main Django application process.**

## 2. Architecture & Data Flow

```text
React (Monaco Editor)
        ↓  POST /api/submissions/run/ or /submit/
Django REST Framework API
        ↓  CodeExecutionService
Docker Sandbox Container / Subprocess Sandbox
        ↓  Isolated temporary workspace (tempfile.TemporaryDirectory)
Run Code Against Test Cases (solution.py + runner.py)
        ↓  Return JSON results & runtime metrics
Django Database (PostgreSQL)
        ↓  Update UserProblemProgress & Submission Log
React UI Response
```

## 3. Execution Sandboxing Modes

### Primary Mode: Docker Container Execution
When Docker CLI is present on the host system, code runs inside an ephemeral Docker container:
* **Container Image:** `python:3.11-slim`
* **Command:** `docker run --rm -v <temp_dir>:/app:ro -w /app --network none --memory 128m python:3.11-slim python3 runner.py`
* **Security Controls:**
  * `--network none`: Complete network isolation. Student code cannot make outbound HTTP requests or open network sockets.
  * `--memory 128m`: Strict memory cap preventing RAM exhaustion or fork-bomb OOM attacks.
  * `-v <temp_dir>:/app:ro`: Read-only host volume mount preventing filesystem modification outside the temporary workspace.
  * Execution Timeout: Hard limit of **4.0 seconds** per execution run.

### Secondary Fallback: Subprocess Isolation
If Docker CLI is unavailable on the host environment, execution safely falls back to a restricted Python subprocess (`subprocess.Popen` / `subprocess.run`):
* Isolated temporary workspace created per invocation via `tempfile.TemporaryDirectory()`.
* Timeout protection enforced via `timeout=4.0` in `subprocess.run()`.
* Output sterilization and error stack trace sanitization (`_sanitize_error_stack`) to prevent exposing internal host directory structures to the client.

## 4. Run vs. Submit Workflow

| Action | API Endpoint | Test Cases Executed | Data Persistence | Progress Update |
| :--- | :--- | :--- | :--- | :--- |
| **Run** | `POST /api/submissions/run/` | Public Test Cases (`is_public=True`) | None (ephemeral) | No progress change |
| **Submit** | `POST /api/submissions/submit/` | All Test Cases (Public + Hidden) | Persisted in `submissions` table | Updates `UserProblemProgress` to `SOLVED` (if Accepted) or `ATTEMPTED` |

## 5. Submission Status Definitions
* `ACCEPTED`: All test cases passed successfully within limits.
* `WRONG_ANSWER`: Code ran without error, but output did not match expected testcase output.
* `RUNTIME_ERROR`: Exceptions thrown during execution (e.g., `IndexError`, `TypeError`, `ZeroDivisionError`).
* `SYNTAX_ERROR`: Code fails to compile or parse.
* `TIME_LIMIT_EXCEEDED`: Execution exceeded 4.0 second limit.
* `INTERNAL_ERROR`: Execution service failure or invalid input payload.
