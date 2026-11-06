"""NGƯỜI 1 — PHẦN A: PAGERANK (30 ĐIỂM)

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


# ====================================================================
# PHẦN A: PAGERANK (30 ĐIỂM) | TODO A1 | NGƯỜI 1
# HÀM: load_graph()
# NHIỆM VỤ: Đọc articles.tsv và links.tsv, xây dựng đồ thị có hướng.
# LIÊN KẾT: Đầu ra (ids, out_neighbors) được pagerank() sử dụng; Người 2 cần kết quả phần A để chạy phần B.
# LƯU Ý: Giữ nguyên docstring, tham số, kiểu trả về và quy tắc xử lý lỗi.
# ====================================================================
def load_graph(
    articles_path: Path, links_path: Path
) -> tuple[list[str], list[list[int]]]:
    """Đọc tập đỉnh và danh sách cạnh từ hai tệp TSV UTF-8.

    Bỏ dòng trống/dòng bắt đầu bằng #. Giữ ID mã hóa phần trăm.
    Trả (ids, out_neighbors): ids là danh sách ID phân biệt sắp theo byte
    UTF-8; out_neighbors[j] chứa các chỉ số đích của đỉnh ids[j].
    Gộp cạnh trùng, giữ cạnh tự nối và mọi đỉnh trong articles.tsv.
    Nút cụt có danh sách đích rỗng. Không gắn cứng số đỉnh/cạnh.
    Báo ValueError nếu đồ thị rỗng hoặc cạnh chứa ID ngoài tập đỉnh.
    """
    # TODO: Sinh viên cài đặt.
    raise NotImplementedError("Chưa cài đặt load_graph")


# ====================================================================
# PHẦN A: PAGERANK (30 ĐIỂM) | TODO A2–A4 | NGƯỜI 1
# HÀM: pagerank()
# NHIỆM VỤ: Tính PageRank bằng power iteration, xử lý dangling node, teleport và hội tụ.
# LIÊN KẾT: PHẢI hỗ trợ teleport=None và teleport tùy chọn để Người 2 tính Topic-sensitive PageRank.
# LƯU Ý: Giữ nguyên docstring, tham số, kiểu trả về và quy tắc xử lý lỗi.
# ====================================================================
def pagerank(
    ids: list[str],
    out_neighbors: list[list[int]],
    beta: float,
    tol: float,
    max_iter: int,
    teleport: list[float] | None = None,
) -> list[float]:
    """Tính PageRank toàn cục hoặc theo phân phối dịch chuyển cho trước.

    ids và out_neighbors dùng cùng chỉ số như kết quả load_graph.
    beta thuộc (0, 1), tol > 0, max_iter là số nguyên >= 1.
    teleport=None dùng phân phối đều; nếu có, teleport phải dài len(ids),
    hữu hạn, không âm và có tổng lệch 1 không quá 1e-12.
    Khởi tạo bằng phân phối dịch chuyển; bù nút cụt luôn đều trên mọi đỉnh.
    Cập nhật đồng thời bằng số thực 64 bit. Dừng khi sai khác L1 giữa hai
    vòng <= tol hoặc đã thực hiện max_iter vòng; không chuẩn hóa lại.
    Trả vector mới nhất theo thứ tự ids, không trả thống kê phụ.
    Báo ValueError nếu tham số hoặc phân phối dịch chuyển không hợp lệ.
    """
    # TODO: Sinh viên cài đặt.
    raise NotImplementedError("Chưa cài đặt pagerank")


