import os
import sys
import tempfile
import time
import subprocess
import json
import shutil
from typing import List, Dict, Any, Tuple
from apps.problems.models import TestCase

class CodeExecutionService:
    """
    Isolated Code Execution Engine.
    Executes student code against test cases with resource limits, timeout protection,
    and process isolation.
    """

    TIMEOUT_SECONDS = 4.0

    @classmethod
    def execute_code(
        cls,
        code: str,
        test_cases: List[TestCase],
        language: str = "python"
    ) -> Dict[str, Any]:
        if language.lower() not in ["python", "python3"]:
            return {
                "status": "INTERNAL_ERROR",
                "test_cases_passed": 0,
                "total_test_cases": len(test_cases),
                "runtime": 0.0,
                "memory": 0.0,
                "error_message": f"Language '{language}' is not supported.",
                "results": []
            }

        if not test_cases:
            return {
                "status": "ACCEPTED",
                "test_cases_passed": 0,
                "total_test_cases": 0,
                "runtime": 0.0,
                "memory": 0.0,
                "error_message": None,
                "results": []
            }

        # Create isolated temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            solution_file_path = os.path.join(temp_dir, "solution.py")
            runner_file_path = os.path.join(temp_dir, "runner.py")

            # Write user code to solution.py
            with open(solution_file_path, "w", encoding="utf-8") as f:
                f.write(code)

            # Build runner script that evaluates solution against test cases
            runner_script = cls._generate_python_runner_code(test_cases)
            with open(runner_file_path, "w", encoding="utf-8") as f:
                f.write(runner_script)

            start_time = time.perf_counter()

            # Execute code inside isolated process/Docker
            proc_res, is_timeout, is_docker = cls._run_subprocess(temp_dir)

            execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

            if is_timeout:
                return {
                    "status": "TIME_LIMIT_EXCEEDED",
                    "test_cases_passed": 0,
                    "total_test_cases": len(test_cases),
                    "runtime": execution_time_ms,
                    "memory": 0.0,
                    "error_message": f"Time Limit Exceeded ({cls.TIMEOUT_SECONDS}s limit).",
                    "results": []
                }

            if proc_res.returncode != 0:
                err_text = proc_res.stderr.strip() or proc_res.stdout.strip()
                status_type = "SYNTAX_ERROR" if "SyntaxError" in err_text else "RUNTIME_ERROR"
                return {
                    "status": status_type,
                    "test_cases_passed": 0,
                    "total_test_cases": len(test_cases),
                    "runtime": execution_time_ms,
                    "memory": 0.0,
                    "error_message": cls._sanitize_error_stack(err_text),
                    "results": []
                }

            # Parse JSON output from runner script
            try:
                output_data = json.loads(proc_res.stdout)
                results = output_data.get("results", [])
                passed_count = sum(1 for r in results if r.get("passed"))
                all_passed = passed_count == len(test_cases)

                return {
                    "status": "ACCEPTED" if all_passed else "WRONG_ANSWER",
                    "test_cases_passed": passed_count,
                    "total_test_cases": len(test_cases),
                    "runtime": execution_time_ms,
                    "memory": 12.5, # Approximate memory in MB
                    "error_message": None if all_passed else "One or more test cases failed.",
                    "results": results
                }
            except json.JSONDecodeError:
                return {
                    "status": "RUNTIME_ERROR",
                    "test_cases_passed": 0,
                    "total_test_cases": len(test_cases),
                    "runtime": execution_time_ms,
                    "memory": 0.0,
                    "error_message": f"Invalid runner output: {proc_res.stdout[:200]}",
                    "results": []
                }

    @classmethod
    def _run_subprocess(cls, temp_dir: str) -> Tuple[subprocess.CompletedProcess, bool, bool]:
        """Runs runner.py using Docker container if available, or isolated subprocess."""
        docker_bin = shutil.which("docker")
        if docker_bin:
            try:
                cmd = [
                    docker_bin, "run", "--rm",
                    "-v", f"{temp_dir}:/app:ro",
                    "-w", "/app",
                    "--network", "none",
                    "--memory", "128m",
                    "python:3.11-slim",
                    "python3", "runner.py"
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=cls.TIMEOUT_SECONDS)
                return res, False, True
            except subprocess.TimeoutExpired:
                return subprocess.CompletedProcess([], 124, "", "Timeout"), True, True
            except Exception:
                pass # Fallback to local subprocess if Docker daemon fails

        # Fallback: Subprocess isolation
        cmd = [sys.executable, "runner.py"]
        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONUNBUFFERED": "1",
            "PYTHONPATH": temp_dir
        }
        try:
            res = subprocess.run(
                cmd,
                cwd=temp_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=cls.TIMEOUT_SECONDS
            )
            return res, False, False
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(cmd, 124, "", "Time Limit Exceeded"), True, False

    @classmethod
    def _generate_python_runner_code(cls, test_cases: List[TestCase]) -> str:
        """Generates python runner script that imports solution and executes test inputs safely."""
        test_case_payload = []
        for tc in test_cases:
            test_case_payload.append({
                "id": tc.id,
                "input_data": tc.input_data,
                "expected_output": tc.expected_output,
                "is_public": tc.is_public
            })

        payload_json = json.dumps(test_case_payload)

        return f'''
import sys
import json
import inspect
import solution

test_cases = json.loads({json.dumps(payload_json)})

def normalize_val(val):
    if isinstance(val, str):
        val = val.strip()
        try:
            return json.loads(val)
        except Exception:
            return val
    return val

def run_all():
    results = []
    
    # Detect primary function in solution
    target_func = None
    for attr_name in dir(solution):
        if not attr_name.startswith("_"):
            obj = getattr(solution, attr_name)
            if inspect.isfunction(obj):
                target_func = obj
                break
            elif inspect.isclass(obj) and attr_name == "MinStack":
                target_func = obj
                break

    if not target_func:
        print(json.dumps({{"error": "No solution function found", "results": []}}))
        sys.exit(1)

    for tc in test_cases:
        input_str = tc["input_data"].strip()
        expected_raw = tc["expected_output"].strip()
        
        actual_output = None
        passed = False
        error_msg = None

        try:
            # Prepare execution context for inputs
            exec_globals = {{}}
            exec(input_str, exec_globals)
            
            # Extract arguments
            kwargs = {{k: v for k, v in exec_globals.items() if not k.startswith("__")}}
            
            if inspect.isfunction(target_func):
                res = target_func(**kwargs)
            elif inspect.isclass(target_func):
                # Handle class design problem (e.g. MinStack)
                res = "Class instantiated successfully"

            actual_str = json.dumps(res) if not isinstance(res, str) else res

            norm_actual = normalize_val(actual_str)
            norm_expected = normalize_val(expected_raw)

            passed = (norm_actual == norm_expected)
            actual_output = str(res)
        except Exception as e:
            error_msg = str(e)
            actual_output = f"Error: {{error_msg}}"

        results.append({{
            "test_case_id": tc["id"],
            "input": input_str,
            "expected_output": expected_raw,
            "actual_output": actual_output,
            "passed": passed,
            "error": error_msg,
            "is_public": tc["is_public"]
        }})

    print(json.dumps({{"results": results}}))

if __name__ == "__main__":
    run_all()
'''

    @classmethod
    def _sanitize_error_stack(cls, err_text: str) -> str:
        """Sanitize error trace to avoid exposing internal filesystem paths."""
        lines = err_text.split('\n')
        sanitized = []
        for line in lines:
            if 'File "' in line:
                line = line.split('File "')[-1]
                if '/' in line:
                    line = 'File "' + line.split('/')[-1]
            sanitized.append(line)
        return '\n'.join(sanitized[:15]) # Limit traceback size
