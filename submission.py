"""Mẫu bài nộp Wikispeedia — Python 3.10 trở lên.

Hoàn thiện các hàm có TODO; giữ tên hàm, tham số và kiểu đầu ra.
main() đã có phần điều phối và ghi bốn tệp CSV theo đề bài.
Mẫu chưa hoàn thiện sẽ báo NotImplementedError, không sinh đáp án giả.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import math
import numbers
import hashlib

import sys

reconfigure = getattr(sys.stdout, "reconfigure", None)
if reconfigure is not None:
    reconfigure(encoding="utf-8")


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


def normalize_text(text: str) -> str:
    r"""Chuẩn hóa chuỗi Unicode theo đúng quy tắc của phần C.

    Chỉ đổi ASCII A–Z thành a–z. Gộp mỗi dãy ký tự thuộc tập dấu cách
    ASCII, \t, \n, \r, \v, \f thành một dấu cách ASCII; bỏ dấu cách ASCII
    ở hai đầu. Giữ nguyên các ký tự khác, dấu câu và toàn bộ nội dung.
    Không chuẩn hóa Unicode, bỏ dấu hoặc gọi lower() cho toàn bộ Unicode.
    Trả chuỗi đã chuẩn hóa; chuỗi rỗng hoặc chỉ có khoảng trắng trên trả ''.
    """
    # TODO: Sinh viên cài đặt.
    trans_table = str.maketrans(
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        'abcdefghijklmnopqrstuvwxyz'
    )
    text = text.translate(trans_table)

    result = []
    whitespace = " \t\n\r\v\f"

    for char in text:
        if char in whitespace:
            if result and result[-1] != " ":
                result.append(" ")
        else:
            result.append(char)

    if result and result[-1] == " ":
        result.pop()

    return "".join(result)


def shingles(text: str, k: int) -> set[str]:
    """Tạo tập k-shingle từ chuỗi ĐÃ được normalize_text xử lý.

    Mỗi shingle là k code point Unicode liên tiếp, không phải k byte/từ.
    Trả tập chuỗi phân biệt; không lưu số lần xuất hiện hoặc vị trí.
    Chuỗi ngắn hơn k trả tập rỗng. Báo ValueError nếu k không phải số
    nguyên dương. Không chuẩn hóa văn bản thêm lần nữa trong hàm này.
    """
    # TODO: Sinh viên cài đặt.
    if not isinstance(k, int) or isinstance(k, bool) or k <= 0:
        raise ValueError("k phải là số nguyên dương")
    if len(text) < k: return set()
    return {text[i:i + k] for i in range(len(text) - k + 1)}


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
        min_val = min(
        (a * x + b) % p
        for x in shingle_ids
        )
        signature.append(min_val)
    return signature


def jaccard(set_a: set[str], set_b: set[str]) -> float:
    """Tính Jaccard chính xác trên hai tập CHUỖI shingle trước bước băm.

    Trả kích thước giao chia kích thước hợp. Theo quy ước bài tập, hai tập
    rỗng trả 1.0; chỉ một tập rỗng trả 0.0. Không dùng tập mã băm thay thế.
    """
    # TODO: Sinh viên cài đặt.
    if not set_a and not set_b:
        return 1.0

    if not set_a or not set_b:
        return 0.0

    intersection = len(set_a & set_b)
    union = len(set_a) + len(set_b) - intersection

    return intersection / union


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
    if (len(sig_a) != len(sig_b)) or len(sig_a) <= 0:
        raise ValueError
    if empty_a and empty_b:
        return 1.0
    if empty_a or empty_b:
        return 0.0
    matches = sum(1 for x, y in zip(sig_a, sig_b) if x == y)
    return float(matches / len(sig_a))


def main() -> None:
    """Đọc tham số, gọi các hàm sinh viên và ghi bốn tệp kết quả CSV.

    Chạy từ thư mục gốc bài tập sau khi giải nén dữ liệu vào data/.
    Dùng --help để xem tùy chọn. Import tệp không tự chạy xử lý dữ liệu.
    Khi các hàm TODO đã hoàn thiện, main tạo pagerank.csv,
    topic_pagerank.csv, minhash.csv và similarities.csv trong --output-dir.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument(
        "--hash-params", type=Path, default=Path("assignment/minhash_params.json")
    )
    parser.add_argument(
        "--pairs", type=Path, default=Path("data/pairs.csv"),
        help="CSV có header article_id_a,article_id_b; mặc định dùng bộ cặp Wikispeedia chính thức.",
    )
    parser.add_argument("--beta", type=float, default=0.85)
    parser.add_argument("--tol", type=float, default=1e-10)
    parser.add_argument("--max-iter", type=int, default=1000)
    args = parser.parse_args()

    graph_dir = args.data_dir / "wikispeedia_paths-and-graph"
    text_dir = args.data_dir / "plaintext_articles"
    with args.hash_params.open(encoding="utf-8") as handle:
        hash_params = json.load(handle)
    with args.pairs.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["article_id_a", "article_id_b"]:
            raise ValueError("Tệp cặp cần header article_id_a,article_id_b")
        pairs = [(row["article_id_a"], row["article_id_b"]) for row in reader]

    ids, out_neighbors = load_graph(
        graph_dir / "articles.tsv", graph_dir / "links.tsv"
    )
    required_ids = {article for pair in pairs for article in pair}
    if not required_ids.issubset(set(ids)):
        raise ValueError("Tệp cặp chứa ID không có trong articles.tsv")

    # A. Điểm PageRank toàn cục.
    scores = pagerank(ids, out_neighbors, args.beta, args.tol, args.max_iter)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "pagerank.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(["article_id", "score"])
        for i, article in enumerate(ids):
            writer.writerow([article, format(scores[i], ".17g")])

    # B. Ba chủ đề và r_mix trong cùng một tệp.
    topics = ["Science", "History", "Geography"]
    topic_scores = []
    for topic in topics:
        teleport = topic_distribution(
            ids, graph_dir / "categories.tsv", "subject." + topic
        )
        topic_scores.append(
            pagerank(ids, out_neighbors, args.beta, args.tol, args.max_iter, teleport)
        )
    mixed_scores = mix_pageranks(topic_scores, [0.5, 0.3, 0.2])
    with (args.output_dir / "topic_pagerank.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(["topic", "article_id", "score"])
        for topic, vector in zip(topics + ["r_mix"], topic_scores + [mixed_scores]):
            for i, article in enumerate(ids):
                writer.writerow([topic, article, format(vector[i], ".17g")])

    # C. Chữ ký cho mọi bài; chỉ giữ tập chuỗi cho các cặp cần so sánh.
    signatures = {}
    pair_shingles = {}
    with (args.output_dir / "minhash.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle)
        length = len(hash_params["hash_functions"])
        writer.writerow(
            ["article_id", "shingle_count"] + [f"h{j:03d}" for j in range(length)]
        )
        for article in ids:
            text = (text_dir / (article + ".txt")).read_text(encoding="utf-8")
            parts = shingles(normalize_text(text), hash_params["shingle_length"])
            codes = {shingle_id(part, hash_params["p"]) for part in parts}
            signature = minhash(codes, hash_params)
            signatures[article] = signature
            if article in required_ids:
                pair_shingles[article] = parts
            writer.writerow([article, len(parts), *signature])

    with (args.output_dir / "similarities.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["article_id_a", "article_id_b", "jaccard_exact", "jaccard_estimate"]
        )
        for article_a, article_b in pairs:
            set_a, set_b = pair_shingles[article_a], pair_shingles[article_b]
            exact = jaccard(set_a, set_b)
            estimate = signature_similarity(
                signatures[article_a], signatures[article_b], not set_a, not set_b
            )
            writer.writerow(
                [article_a, article_b, format(exact, ".17g"), format(estimate, ".17g")]
            )

    print(f"Đã ghi bốn tệp kết quả vào {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
