import os
import unittest
import sys
from app.execution.sandbox import run_transform

class TestSandbox(unittest.TestCase):
    def setUp(self):
        self.input_path = "tests/test_input.xlsx"
        self.output_path = "tests/test_output.xlsx"
        os.makedirs("tests", exist_ok=True)
        import pandas as pd
        pd.DataFrame({"A": [1, 2], "B": [3, 4]}).to_excel(self.input_path, index=False)

    def tearDown(self):
        if os.path.exists(self.input_path):
            os.remove(self.input_path)
        if os.path.exists(self.output_path):
            os.remove(self.output_path)

    def test_successful_execution(self):
        code = """
def transform(input_path, output_path):
    import pandas as pd
    df = pd.read_excel(input_path)
    df['C'] = df['A'] + df['B']
    df.to_excel(output_path, index=False)
"""
        result = run_transform(code, self.input_path, self.output_path)
        self.assertTrue(result["success"])
        self.assertIn("---SUCCESS---", result["logs"])
        self.assertTrue(os.path.exists(self.output_path))

    def test_syntax_error(self):
        code = """
def transform(input_path, output_path):
    invalid syntax
"""
        result = run_transform(code, self.input_path, self.output_path)
        self.assertFalse(result["success"])
        self.assertIn("SyntaxError", result["logs"])

    def test_runtime_error(self):
        code = """
def transform(input_path, output_path):
    raise ValueError("Something went wrong")
"""
        result = run_transform(code, self.input_path, self.output_path)
        self.assertFalse(result["success"])
        self.assertIn("ValueError", result["logs"])

    def test_missing_transform_function(self):
        code = """
def not_transform(input_path, output_path):
    pass
"""
        result = run_transform(code, self.input_path, self.output_path)
        self.assertFalse(result["success"])
        self.assertIn("NameError", result["logs"]) # Because transform() call in wrapper will fail

if __name__ == "__main__":
    unittest.main()
