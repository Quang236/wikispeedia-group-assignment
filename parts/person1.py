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
import math

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
    article = set() # loại bỏ id trùng
    with open(articles_path,"r",encoding="utf-8") as f:
        for line in f:
            line = line.strip() # bỏ khoảng trắng
            if not line or line.startswith("#"): #nếu line rỗng hoặc bắt đầu = "#" thì bỏ qua
                continue
            article.add(line) #thêm vào set

    # Sắp xếp tập đỉnh theo thứ tự từ điển của byte UTF-8    
    # Quy ước đề bài: sắp xếp theo biểu diễn byte UTF-8 của tên bài viết
    ids = sorted(article, key=lambda x: x.encode("utf-8"))

    # Báo lỗi ValueError nếu đồ thị rỗng (không có đỉnh nào)
    if not ids:
        raise ValueError("Đồ thị rỗng")

    # Tạo từ điển ánh xạ (ID bài viết -> Chỉ số số nguyên 0..N-1)

    # Tra cứu chỉ số đỉnh thay vì tìm tuyến tính trong list
    id_to_index = {article_id: idx for idx, article_id in enumerate(ids)}

    # Đọc danh sách cạnh từ links.tsv và xây dựng danh sách kề
    # Khởi tạo một set cho mỗi đỉnh:
    # - Tự động loại bỏ cạnh trùng (duplicate edges)
    # - Đỉnh cụt (dangling nodes / out-degree = 0) sẽ giữ nguyên set rỗng
    out_sets = [set() for _ in range(len(ids))]

    with open(links_path,"r",encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Mỗi dòng có dạng: source<TAB>target
            source, target = line.split("\t")

            # Báo lỗi nếu đầu mút không thuộc tập đỉnh trong articles.tsv
            if source not in id_to_index or target not in id_to_index:
                raise ValueError(f"Cạnh chứa ID ngoài tập đỉnh: ({source} -> {target})")

            source_idx = id_to_index[source]
            target_idx = id_to_index[target]

            # Thêm đỉnh đích vào tập lân cận đi ra của đỉnh nguồn (giữ cả self-loop)
            out_sets[source_idx].add(target_idx)

        out_neighbours = [sorted(i) for i in out_sets]

    return ids,out_neighbours
        
            


# ====================================================================
# PHẦN A: PAGERANK (30 ĐIỂM) | TODO A2–A4 | NGƯỜI 1
# HÀM: pagerank()
# NHIỆM VỤ: Tính PageRank bằng power iteration, xử lý dangling node, teleport và hội tụ.
# LIÊN KẾT: PHẢI hỗ trợ teleport=None và teleport tùy chọn để Người 2 tính Topic-sensitive PageRank.
# LƯU Ý: Giữ nguyên docstring, tham số, kiểu trả về và quy tắc xử lý lỗi.
# ====================================================================
def pagerank(
    ids: list[str], #ds các đỉnh của đồ thị
    out_neighbors: list[list[int]], #ds các đích đến (ds kề)
    beta: float, #xác suất đi theo lk
    tol: float, #ngưỡng sai số để dừng
    max_iter: int, #số vòng lặp tối đa
    teleport: list[float] | None = None, #phân phối xs nhảy ngẫu nhiên
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
    #check điều kiện tham số truyền vào 
    if not (0<beta<1):
        raise ValueError("beta không hợp lệ, cần trong khoảng 0-1")
    if not (tol > 0):
        raise ValueError("Tol không hợp lệ, cần là số dương")
    if type(max_iter) is not int or max_iter <1:
        raise ValueError("max_iter không hợp lệ")

    n = len(ids) #số đỉnh
    if teleport is None: # không có teleport
        v = [1/n for _ in range(n)]
    else: #sensitive-pagerank
        if len(teleport) != n:
            raise ValueError(" Độ dài teleport không hợp lệ")
        for p in teleport:
            if p < 0 or not math.isfinite(p):
                raise ValueError(" Giá trị của teleport không hợp lệ")
        if abs(sum(teleport)-1) > 1e-12:
            raise ValueError(" Tổng xác suất teleport không hợp lệ")
        v = list(teleport)
    
    r = v.copy()

    for _ in range(max_iter):
        r_new = [0.0 for _ in range(n)]
        dinh_cut = 0.0
        for j in range(n):
            if not out_neighbors[j]:
                dinh_cut += r[j]
        bu_nut_cut = (beta* dinh_cut) / n
        for i in range(n):
            r_new[i] = bu_nut_cut + (1-beta)*v[i]

        # điểm từ các liên kết
        for s in range(n):
            neighbour = out_neighbors[s]
            if not neighbour:
                continue
            diem_tu_lk = beta* (r[s]/len(neighbour))
            for target in neighbour:
                r_new[target] += diem_tu_lk
        
        error = 0.0
        for l in range(n):
            error += abs(r_new[l]-r[l])
        r = r_new
        if error <= tol:
            break


    return r
        

