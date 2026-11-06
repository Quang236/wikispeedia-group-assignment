#!/usr/bin/env python3
"""Ghép 3 file parts/*.py vào submission_template.py mà không đụng vào main().

Chỉ các hàm được phân công mới thay thế hàm TODO; giữ nguyên docstring,
chữ ký và thứ tự của template. Import/hàm phụ ở cấp module được bổ sung.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "assignment/submission_template.py"
OUTPUT = ROOT / "submission.py"
OWNERS = {
    # Chia trọn vẹn theo thuật toán/phần của đề:
    "person1.py": ("load_graph", "pagerank"),  # A
    "person2.py": ("topic_distribution", "mix_pageranks"),  # B
    "person3.py": (  # C
        "normalize_text", "shingles", "shingle_id",
        "minhash", "jaccard", "signature_similarity",
    ),
}


def main() -> None:
    source = TEMPLATE.read_text(encoding="utf-8")
    reference_tree = ast.parse(source)
    ref_functions = {
        n.name: n for n in reference_tree.body if isinstance(n, ast.FunctionDef)
    }
    seen = set()
    replacements = {}
    extra_imports = []
    helpers = []
    helper_names = set()
    template_imports = {
        ast.get_source_segment(source, n).strip()
        for n in reference_tree.body
        if isinstance(n, (ast.Import, ast.ImportFrom))
    }

    for filename, owned in OWNERS.items():
        part_source = (ROOT / "parts" / filename).read_text(encoding="utf-8")
        part_tree = ast.parse(part_source, filename=filename)
        found = set()
        for node in part_tree.body:
            if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                continue
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                statement = ast.get_source_segment(part_source, node).strip()
                if statement not in template_imports and statement not in extra_imports:
                    extra_imports.append(statement)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                definition = ast.get_source_segment(part_source, node).rstrip()
                if node.name in owned:
                    if node.name in found:
                        raise ValueError(f"Hàm {node.name} lặp lại ở {filename}")
                    if isinstance(node, ast.AsyncFunctionDef):
                        raise ValueError(f"Không sử dụng async cho {node.name}")
                    # Kiểm tra tên và số / kiểu tham số giữ nguyên như mẫu.
                    sample = ref_functions[node.name]
                    if ast.dump(node.args, include_attributes=False) != ast.dump(sample.args, include_attributes=False):
                        raise ValueError(f"{filename}: chữ ký tham số của {node.name} khác template")
                    if ast.dump(node.returns, include_attributes=False) != ast.dump(sample.returns, include_attributes=False):
                        raise ValueError(f"{filename}: kiểu trả về của {node.name} khác template")
                    replacements[node.name] = definition
                    found.add(node.name)
                    seen.add(node.name)
                elif node.name in ref_functions:
                    raise ValueError(f"{filename}: Không được sửa hàm {node.name} của người khác/main")
                else:
                    if node.name in helper_names:
                        raise ValueError(f"Hàm phụ {node.name} bị trùng giữa các file")
                    helper_names.add(node.name)
                    helpers.append(definition)
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                pass  # module docstring
            elif isinstance(node, ast.Pass):
                pass
            else:
                raise ValueError(
                    f"{filename}: chỉ đặt import, def và docstring ở cấp module; "
                    "chuyển các lệnh chạy thử vào if __name__ == '__main__' riêng "
                    "(không đưa khối đó vào file parts)."
                )
        missing = set(owned) - found
        if missing:
            raise ValueError(f"{filename} thiếu hàm: {sorted(missing)}")
    expected = set(sum((list(v) for v in OWNERS.values()), []))
    if seen != expected:
        raise ValueError(f"Thiếu các hàm: {sorted(expected-seen)}")

    # Thay các đoạn theo thứ tự từ cuối tệp, giữ nguyên main và phần CLI.
    lines = source.splitlines(keepends=True)
    for name,node in sorted(
        ((n,ref_functions[n]) for n in replacements),
        key=lambda entry: entry[1].lineno, reverse=True,
    ):
        lines[node.lineno-1:node.end_lineno] = [replacements[name] + "\n"]
    merged = "".join(lines)

    # Thêm helper defs trước main để các hàm có thể dùng lại trong cùng tệp.
    if helpers:
        parsed = ast.parse(merged)
        main_node = next(n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        merged_lines = merged.splitlines(keepends=True)
        merged_lines.insert(main_node.lineno-1, "\n\n".join(helpers)+"\n\n\n")
        merged = "".join(merged_lines)

    if extra_imports:
        parsed = ast.parse(merged)
        import_nodes = [n for n in parsed.body if isinstance(n,(ast.Import,ast.ImportFrom))]
        insert_at = max(n.end_lineno for n in import_nodes)
        merged_lines = merged.splitlines(keepends=True)
        merged_lines.insert(insert_at, "\n" + "\n".join(extra_imports) + "\n")
        merged = "".join(merged_lines)

    ast.parse(merged, filename="submission.py")
    OUTPUT.write_text(merged, encoding="utf-8")
    print("✅ Đã ghép 10 hàm vào submission.py. main() giữ nguyên.")
    print("Tiếp theo: python3 autograder.py submission.py --report grading_reports/self_check.json")


if __name__ == "__main__":
    main()
