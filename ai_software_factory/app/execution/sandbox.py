import subprocess
import sys
import os
import tempfile
import traceback
from typing import Dict, Any

def run_transform(generated_code: str, input_path: str, output_path: str, timeout: int = 120) -> Dict[str, Any]:
    """
    Executes the generated code in a subprocess to isolate it.
    The code must have a `transform(input_path: str, output_path: str)` function.
    """
    # Make paths absolute so the subprocess can find them
    abs_input = os.path.abspath(input_path)
    abs_output = os.path.abspath(output_path)
    
    # Create a wrapper script to call the transform function
    wrapper_code = f"""
import sys
import os
import traceback
import pandas as pd
import openpyxl

{generated_code}

if __name__ == "__main__":
    try:
        transform("{abs_input}", "{abs_output}")
        print("---SUCCESS---")
    except Exception as e:
        print(f"---FAILURE---")
        print(traceback.format_exc())
        sys.exit(1)
"""

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tmp:
        tmp.write(wrapper_code)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        stdout = result.stdout
        stderr = result.stderr
        
        success = "---SUCCESS---" in stdout and result.returncode == 0
        logs = stdout + "\n" + stderr
        
        return {
            "success": success,
            "logs": logs.strip(),
            "output_path": output_path if success else None
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "logs": f"Execution timed out after {timeout} seconds.",
            "output_path": None
        }
    except Exception as e:
        return {
            "success": False,
            "logs": f"Sandbox execution error: {str(e)}\n{traceback.format_exc()}",
            "output_path": None
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

