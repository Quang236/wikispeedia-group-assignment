"""Người 2 — Topic PageRank và Similarity.

Chỉ sửa các hàm được giao. KHÔNG sửa tên hàm/chữ ký hàm từ đề gốc.
Chạy `python3 build_submission.py` ở thư mục gốc để ghép tự động.
Có thể thêm import và hàm phụ ở cấp module; script ghép sẽ thu thập chúng.
"""

from __future__ import annotations

# Thêm import cần thiết ngay dưới dòng này, ví dụ: import hashlib

# TODO B1–B2 • Chọn prefix chính xác, phân phối đều trong chủ đề.
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
    raise NotImplementedError("Chưa cài đặt topic_distribution")


# TODO B3 • Tổng tuyến tính các vector cùng chiều; kiểm tra weights.
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
    raise NotImplementedError("Chưa cài đặt mix_pageranks")


# TODO C3 • Jaccard trên tập shingle chuỗi; xử lý tập rỗng.
def jaccard(set_a: set[str], set_b: set[str]) -> float:
    """Tính Jaccard chính xác trên hai tập CHUỖI shingle trước bước băm.

    Trả kích thước giao chia kích thước hợp. Theo quy ước bài tập, hai tập
    rỗng trả 1.0; chỉ một tập rỗng trả 0.0. Không dùng tập mã băm thay thế.
    """
    # TODO: Sinh viên cài đặt.
    raise NotImplementedError("Chưa cài đặt jaccard")


# TODO C3 • So tọa độ chữ ký, không biến signature thành set.
def signature_similarity(
    sig_a: list[int], sig_b: list[int], empty_a: bool, empty_b: bool
) -> float:
    """Ước lượng Jaccard bằng tỷ lệ tọa độ chữ ký trùng nhau.

    Hai chữ ký phải cùng độ dài dương, dùng cùng bộ hàm băm và thứ tự.
    empty_a/empty_b cho biết tập shingle gốc có rỗng hay không.
    Hai tập rỗng trả 1.0; chỉ một tập rỗng trả 0.0. Các trường hợp còn
    lại trả số tọa độ bằng nhau chia độ dài chữ ký. Không chuyển chữ ký
    thành tập. Báo ValueError nếu độ dài không hợp lệ.
    """
    # TODO: Sinh viên cài đặt.
    raise NotImplementedError("Chưa cài đặt signature_similarity")


