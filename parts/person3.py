"""NGƯỜI 3 — PHẦN C: SHINGLING, MINHASH & SIMILARITY (35 ĐIỂM)

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
import hashlib

# ====================================================================
# PHẦN C: SHINGLING, MINHASH & SIMILARITY (35 ĐIỂM) | TODO C1 | NGƯỜI 3
# HÀM: normalize_text()
# NHIỆM VỤ: Chuẩn hóa văn bản Unicode theo quy tắc được mô tả trong docstring.
# LIÊN KẾT: Bước đầu của pipeline phần C; đầu ra chuyển sang shingles().
# LƯU Ý: Giữ nguyên docstring, tham số, kiểu trả về và quy tắc xử lý lỗi.
# ====================================================================
def normalize_text(text: str) -> str:
    r"""Chuẩn hóa chuỗi Unicode theo đúng quy tắc của phần C.

    Chỉ đổi ASCII A–Z thành a–z. Gộp mỗi dãy ký tự thuộc tập dấu cách
    ASCII, \t, \n, \r, \v, \f thành một dấu cách ASCII; bỏ dấu cách ASCII
    ở hai đầu. Giữ nguyên các ký tự khác, dấu câu và toàn bộ nội dung.
    Không chuẩn hóa Unicode, bỏ dấu hoặc gọi lower() cho toàn bộ Unicode.
    Trả chuỗi đã chuẩn hóa; chuỗi rỗng hoặc chỉ có khoảng trắng trên trả ''.
    """
    # TODO: Sinh viên cài đặt.
    if not text or not text.strip():
        return ""
    trans_table = str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')
    text = text.translate(trans_table)
    return text


# ====================================================================
# PHẦN C: SHINGLING, MINHASH & SIMILARITY (35 ĐIỂM) | TODO C1 | NGƯỜI 3
# HÀM: shingles()
# NHIỆM VỤ: Tạo tập các đoạn k ký tự Unicode liên tiếp, không phải k từ.
# LIÊN KẾT: Nhận văn bản đã normalize_text(); đầu ra dùng cho jaccard() và shingle_id().
# LƯU Ý: Giữ nguyên docstring, tham số, kiểu trả về và quy tắc xử lý lỗi.
# ====================================================================
def shingles(text: str, k: int) -> set[str]:
    """Tạo tập k-shingle từ chuỗi ĐÃ được normalize_text xử lý.

    Mỗi shingle là k code point Unicode liên tiếp, không phải k byte/từ.
    Trả tập chuỗi phân biệt; không lưu số lần xuất hiện hoặc vị trí.
    Chuỗi ngắn hơn k trả tập rỗng. Báo ValueError nếu k không phải số
    nguyên dương. Không chuẩn hóa văn bản thêm lần nữa trong hàm này.
    """
    # TODO: Sinh viên cài đặt.
    if k <=0: raise ValueError
    if len(text) < k: return set()
    return {text[i:i + k] for i in range(len(text) - k + 1)}


# ====================================================================
# PHẦN C: SHINGLING, MINHASH & SIMILARITY (35 ĐIỂM) | TODO C2 | NGƯỜI 3
# HÀM: shingle_id()
# NHIỆM VỤ: Băm một shingle thành ID bằng SHA-256 và phép modulo p.
# LIÊN KẾT: Nhận shingle từ shingles(); các ID dùng làm đầu vào minhash().
# LƯU Ý: Giữ nguyên docstring, tham số, kiểu trả về và quy tắc xử lý lỗi.
# ====================================================================
def shingle_id(shingle: str, p: int) -> int:
    """Ánh xạ một shingle thành số nguyên trong [0, p-1].

    Băm byte UTF-8 bằng SHA-256, lấy 4 byte đầu, đọc số nguyên không dấu
    big-endian rồi lấy modulo p. Không dùng hash() mặc định của Python.
    Trả int tất định giữa các lần chạy. Báo ValueError nếu p <= 1.
    """
    # TODO: Sinh viên cài đặt.
    if p <= 1: raise ValueError
    shingle_bytes = shingle.encode("utf-8")
    hash_shingle = hashlib.sha256(shingle_bytes).digest() #trả về chuỗi byte nhị phân
    int_value = int.from_bytes(hash_shingle[:4], byteorder='big', signed=False) #byteorder đọc theo thứ tự, signed dấu
    return int_value % p


# ====================================================================
# PHẦN C: SHINGLING, MINHASH & SIMILARITY (35 ĐIỂM) | TODO C2 | NGƯỜI 3
# HÀM: minhash()
# NHIỆM VỤ: Tạo chữ ký MinHash từ tập shingle IDs và bộ tham số băm đã cho.
# LIÊN KẾT: Đầu ra dùng cho signature_similarity().
# LƯU Ý: Giữ nguyên docstring, tham số, kiểu trả về và quy tắc xử lý lỗi.
# ====================================================================
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
    p = hash_params["p"]
    hash_funcs = hash_params["hash_functions"]
    if not shingle_ids:
        return [p] * len(hash_funcs)
    signature = []
    for hf in hash_funcs:
        a = hf["a"]
        b = hf["b"]
        min_val = p
        for x in shingle_ids:
            toa_do = (a * x + b) % p
            min_val = min(toa_do, min_val)
        signature.append(min_val)
    return signature


# ====================================================================
# PHẦN C: SHINGLING, MINHASH & SIMILARITY (35 ĐIỂM) | TODO C3 | NGƯỜI 3
# HÀM: jaccard()
# NHIỆM VỤ: Tính Jaccard chính xác của hai tập shingle dạng chuỗi.
# LIÊN KẾT: Nhận hai tập do shingles() tạo ra; xử lý trường hợp rỗng theo đề.
# LƯU Ý: Giữ nguyên docstring, tham số, kiểu trả về và quy tắc xử lý lỗi.
# ====================================================================
def jaccard(set_a: set[str], set_b: set[str]) -> float:
    """Tính Jaccard chính xác trên hai tập CHUỖI shingle trước bước băm.

    Trả kích thước giao chia kích thước hợp. Theo quy ước bài tập, hai tập
    rỗng trả 1.0; chỉ một tập rỗng trả 0.0. Không dùng tập mã băm thay thế.
    """
    # TODO: Sinh viên cài đặt.
    if (not set_a) and (not set_b):
        return float(1)
    if (not set_a and set_b) or (not set_b and set_a):
        return float(0)
    intersection = (set_a & set_b)
    union = (set_a | set_b)
    return float(len(intersection) / len(union))


# ====================================================================
# PHẦN C: SHINGLING, MINHASH & SIMILARITY (35 ĐIỂM) | TODO C3 | NGƯỜI 3
# HÀM: signature_similarity()
# NHIỆM VỤ: Ước lượng độ tương đồng bằng tỷ lệ tọa độ chữ ký trùng nhau.
# LIÊN KẾT: Nhận chữ ký từ minhash() và cờ hai tập đầu vào rỗng.
# LƯU Ý: Giữ nguyên docstring, tham số, kiểu trả về và quy tắc xử lý lỗi.
# ====================================================================
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
    if empty_a and empty_b:
        return 1.0
    if empty_a or empty_b:
        return 0.0
    if (len(sig_a) != len(sig_b)) or len(sig_a) <= 0:
        raise ValueError
    matches = sum(1 for x, y in zip(sig_a, sig_b) if x == y)
    return float(matches / len(sig_a))