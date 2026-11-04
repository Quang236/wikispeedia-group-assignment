"""Người 3 — MinHash và tích hợp.

Chỉ sửa các hàm được giao. KHÔNG sửa tên hàm/chữ ký hàm từ đề gốc.
Chạy `python3 build_submission.py` ở thư mục gốc để ghép tự động.
Có thể thêm import và hàm phụ ở cấp module; script ghép sẽ thu thập chúng.
"""

from __future__ import annotations

# Thêm import cần thiết ngay dưới dòng này, ví dụ: import hashlib

# TODO C2 • SHA-256 UTF-8, 4 byte đầu big-endian, modulo p.
def shingle_id(shingle: str, p: int) -> int:
    """Ánh xạ một shingle thành số nguyên trong [0, p-1].

    Băm byte UTF-8 bằng SHA-256, lấy 4 byte đầu, đọc số nguyên không dấu
    big-endian rồi lấy modulo p. Không dùng hash() mặc định của Python.
    Trả int tất định giữa các lần chạy. Báo ValueError nếu p <= 1.
    """
    # TODO: Sinh viên cài đặt.
    raise NotImplementedError("Chưa cài đặt shingle_id")


# TODO C2 • Hệ số từ JSON, không phát sinh mới; tập rỗng trả [p,...].
def minhash(shingle_ids: set[int], hash_params: dict) -> list[int]:
    """Tính chữ ký từ tập mã shingle và bộ hàm băm dùng chung.

    hash_params có p và hash_functions là danh sách {'a': int, 'b': int}
    theo thứ tự tọa độ. Mỗi tọa độ là min((a*x+b) % p) trên shingle_ids.
    Tập rỗng trả toàn giá trị p. Trả list[int] dài bằng số hàm băm;
    không gắn cứng 128 vì bộ chấm có thể dùng bộ hệ số nhỏ khác.
    Mã đầu vào thuộc [0, p-1]; phép nhân/cộng/modulo dùng số nguyên chính
    xác. Không sinh hệ số mới, không trả ID phần tử đạt min.
    """
    # TODO: Sinh viên cài đặt.
    raise NotImplementedError("Chưa cài đặt minhash")


