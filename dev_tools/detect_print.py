#!/usr/bin/env python3
import ast
from pathlib import Path

EXCLUDED_DIRS = ["keyboard", "config_manager", "test", "dev_tools"]
EXCLUDED_FILES = ["my_logger.py"]


def get_project_root() -> Path:
    return Path(__file__).parent.parent


def is_excluded(path: Path) -> bool:
    parts = path.parts
    for excluded_dir in EXCLUDED_DIRS:
        if excluded_dir in parts:
            return True
    if path.name in EXCLUDED_FILES:
        return True
    return False


class PrintDetector(ast.NodeVisitor):
    def __init__(self):
        self.print_lines = []

    def visit_Call(self, node):
        func = node.func
        if isinstance(func, ast.Name):
            if func.id in ("print", "pprint"):
                self.print_lines.append(node.lineno)
        self.generic_visit(node)


def find_print_statements(file_path: Path) -> list[int]:
    try:
        source = file_path.read_text()
    except (UnicodeDecodeError, OSError):
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    detector = PrintDetector()
    detector.visit(tree)
    return detector.print_lines


def main():
    root = get_project_root()
    results = []

    for py_file in root.rglob("*.py"):
        if is_excluded(py_file):
            continue

        lines = find_print_statements(py_file)
        if lines:
            rel_path = py_file.relative_to(root)
            results.append((str(rel_path), lines))

    for file_path, line_numbers in results:
        print(file_path)
        for line_num in line_numbers:
            print(f'line #{line_num}')
        print()


if __name__ == "__main__":
    main()
