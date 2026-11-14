"""NGƯỜI 2 — PHẦN B: TOPIC-SENSITIVE PAGERANK (30 ĐIỂM)

PHÂN CÔNG: Chỉ viết các hàm TODO trong file này.
HƯỚNG DẪN:
- Mỗi hàm được đánh dấu PHẦN, mã TODO và nhiệm vụ cụ thể.
- Docstring là yêu cầu kỹ thuật từ submission_template.py của giảng viên.
- Không đổi tên hàm, chữ ký tham số, annotation kiểu trả về.
- Có thể thêm import và hàm phụ; không viết lệnh thực thi ở cấp module.
- Không sửa submission.py trực tiếp: ghép bằng python3 build_submission.py.

KIỂM THỬ:
- Viết test dữ liệu nhỏ cho từng hàm ngay khi hoàn thành.
- Phần B gọi pagerank() của phần A nên khi test tích hợp B phải có A.
- Autograder tổng hợp có thể báo lỗi ở các phần còn TODO: đó là bình thường.
"""

from __future__ import annotations
from pathlib import Path

# TODO (nếu cần): thêm các import của Python standard library tại đây.
import math
import numbers


# ====================================================================
# PHẦN B: TOPIC-SENSITIVE PAGERANK (30 ĐIỂM) | TODO B1–B2 | NGƯỜI 2
# HÀM: topic_distribution()
# NHIỆM VỤ: Đọc categories.tsv và tạo vector teleport theo chủ đề.
# LIÊN KẾT: Dùng ids từ load_graph() của Người 1; vector truyền cho pagerank(..., teleport=...).
# LƯU Ý: Giữ nguyên docstring, tham số, kiểu trả về và quy tắc xử lý lỗi.
# ====================================================================
def topic_distribution(
    ids: list[str], categories_path: Path, prefix: str
) -> list[float]:
    """Tạo phân phối dịch chuyển đều trên tập trang thuộc một chủ đề.

    Đọc categories.tsv UTF-8, bỏ dòng trống/dòng bắt đầu bằng #.
    Chọn nhãn bằng prefix hoặc bắt đầu bằng prefix + '.'. Một ID chỉ
    được đếm một lần trong tập chủ đề, dù có nhiều nhãn phù hợp.
    Trả vector dài len(ids), theo thứ tự ids: trang thuộc tập nhận 1/|S|,
    trang còn lại nhận 0. Báo ValueError nếu tập chủ đề rỗng hoặc dữ liệu
    nhãn tham chiếu ID ngoài ids. Không dùng nội dung bài để suy ra nhãn.
    """
    # TODO: Sinh viên cài đặt.
    if not ids:
        raise ValueError("Danh sách ids không được rỗng")
    if not isinstance(prefix, str) or not prefix.strip():
        raise ValueError("Tiền tố chủ đề (prefix) không hợp lệ")

    known_ids = set(ids)
    if len(known_ids) != len(ids):
        raise ValueError("Danh sách ids chứa phần tử trùng lặp")

    selected: set[str] = set()
    sub_prefix = prefix + "."

    with open(categories_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split("\t")
            if len(parts) != 2:
                raise ValueError(f"Dòng không đúng định dạng TSV 2 cột: {line!r}")

            article_id, category = parts
            if article_id not in known_ids:
                raise ValueError(
                    f"Dữ liệu nhãn tham chiếu ID ngoài tập đỉnh ids: {article_id!r}"
                )

            if category == prefix or category.startswith(sub_prefix):
                selected.add(article_id)

    if not selected:
        raise ValueError(f"Tập chủ đề rỗng với prefix: {prefix!r}")

    prob = 1.0 / len(selected)
    return [prob if article_id in selected else 0.0 for article_id in ids]


# ====================================================================
# PHẦN B: TOPIC-SENSITIVE PAGERANK (30 ĐIỂM) | TODO B3 | NGƯỜI 2
# HÀM: mix_pageranks()
# NHIỆM VỤ: Kết hợp các vector điểm theo trọng số 0.5, 0.3, 0.2 cho 3 chủ đề.
# LIÊN KẾT: Dùng kết quả pagerank() từ phần A với từng teleport; giữ cùng thứ tự ids.
# LƯU Ý: Giữ nguyên docstring, tham số, kiểu trả về và quy tắc xử lý lỗi.
# ====================================================================
def mix_pageranks(
    topic_scores: list[list[float]], weights: list[float]
) -> list[float]:
    """Ghép các vector PageRank bằng tổng có trọng số theo từng tọa độ.

    topic_scores gồm các vector cùng độ dài, cùng thứ tự đỉnh.
    weights có một trọng số cho mỗi vector, hữu hạn, không âm và có
    tổng lệch 1 không quá 1e-12. Trả một vector có cùng độ dài.
    Cấu hình chính thức dùng thứ tự Science, History, Geography và trọng
    số 0.5, 0.3, 0.2. Không chạy lại PageRank hoặc làm tròn điểm ở đây.
    Báo ValueError nếu danh sách rỗng, kích thước hoặc trọng số không hợp lệ.
    """
    # TODO: Sinh viên cài đặt.
    if not topic_scores or not weights:
        raise ValueError("Danh sách topic_scores và weights không được rỗng")
    if len(topic_scores) != len(weights):
        raise ValueError("Số lượng vector điểm và số lượng trọng số không khớp")

    for w in weights:
        if (
            not isinstance(w, numbers.Real)
            or isinstance(w, bool)
            or not math.isfinite(w)
            or w < 0
        ):
            raise ValueError(f"Trọng số không hợp lệ: {w!r}")

    if abs(math.fsum(weights) - 1.0) > 1e-12:
        raise ValueError("Tổng các trọng số lệch 1 quá 1e-12")

    n = len(topic_scores[0])
    if n == 0:
        raise ValueError("Vector điểm không được rỗng")

    for vec in topic_scores:
        if len(vec) != n:
            raise ValueError("Các vector trong topic_scores phải có cùng độ dài")
        for val in vec:
            if (
                not isinstance(val, numbers.Real)
                or isinstance(val, bool)
                or not math.isfinite(val)
            ):
                raise ValueError(f"Giá trị điểm không hợp lệ: {val!r}")

    return [
        math.fsum(w * vec[i] for w, vec in zip(weights, topic_scores))
        for i in range(n)
    ]


