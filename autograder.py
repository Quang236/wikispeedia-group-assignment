"""Chấm bài Wikispeedia theo 13 dòng tiêu chí, tổng 100 điểm.

Python 3.10+, chỉ dùng thư viện chuẩn. Không import solution.py làm đáp án.
Mỗi dòng tiêu chí được kiểm tra trong một tiến trình riêng có timeout.
Đây là công cụ chạy mã cục bộ, không phải môi trường cách ly mã không tin cậy.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import importlib.util
import json
import math
import numbers
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import tarfile
import tempfile
import traceback

ROOT = Path(__file__).resolve().parent
RUBRIC = [
    ("A1", 5, "Đọc đồ thị"),
    ("A2", 8, "Một vòng PageRank"),
    ("A3", 12, "Nghiệm PageRank: đồ thị nhỏ và Wikispeedia"),
    ("A4", 5, "Dừng và bất biến xác suất"),
    ("B1", 6, "Tập chủ đề và phân phối dịch chuyển"),
    ("B2", 10, "Cập nhật theo chủ đề và bù nút cụt"),
    ("B3", 9, "Nghiệm ba chủ đề"),
    ("B4", 5, "Ghép các vector chủ đề"),
    ("C1", 8, "Chuẩn hóa và shingle"),
    ("C2", 17, "Mã băm và chữ ký MinHash"),
    ("C3", 6, "Jaccard và tương đồng chữ ký"),
    ("C4", 4, "Trường hợp biên và tính chất MinHash"),
    ("IO", 5, "Chạy main, bốn CSV và tính tái lập"),
]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def close(actual, expected, tolerance=1e-12):
    require(isinstance(actual, numbers.Real) and not isinstance(actual, bool),
            "Giá trị phải là số thực hữu hạn")
    require(math.isfinite(actual) and abs(actual - expected) <= tolerance,
            f"Nhận {actual!r}; cần {expected!r}, dung sai {tolerance}")


def vector(actual, expected, tolerance=1e-8):
    require(len(actual) == len(expected), "Sai kích thước vector")
    require(all(isinstance(x, numbers.Real) and not isinstance(x, bool)
                and math.isfinite(x) for x in actual), "Vector chứa số không hợp lệ")
    error = math.fsum(abs(a - b) for a, b in zip(actual, expected))
    require(error <= tolerance, f"Sai khác L1 = {error:.6g} > {tolerance}")


def integers(actual, expected):
    require(len(actual) == len(expected), "Sai độ dài chữ ký")
    require(all(isinstance(x, numbers.Integral) and not isinstance(x, bool)
                for x in actual), "Chữ ký phải chứa số nguyên, không phải float")
    require(list(actual) == expected, "Chữ ký không khớp từng số nguyên")


def raises_value_error(function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except ValueError:
        return
    raise AssertionError("Đầu vào không hợp lệ phải báo ValueError")


def import_submission(path):
    spec = importlib.util.spec_from_file_location("student_submission", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dataset_text(data_dir, relative):
    """Đọc dữ liệu đã giải nén hoặc đọc thành viên tar, không giải nén ra đĩa."""
    for base in [data_dir, data_dir / "extracted"]:
        path = base / relative
        if path.is_file():
            return path.read_text(encoding="utf-8")
    archive = ("wikispeedia_articles_plaintext.tar.gz"
               if relative.startswith("plaintext_articles/")
               else "wikispeedia_paths-and-graph.tar.gz")
    with tarfile.open(data_dir / archive, "r:gz") as handle:
        member = handle.extractfile(relative)
        if member is None:
            raise ValueError(f"Không có tệp {relative}")
        return member.read().decode("utf-8")


def records(text):
    return [line for line in text.splitlines() if line and not line.startswith("#")]


def wiki_graph(data_dir):
    prefix = "wikispeedia_paths-and-graph/"
    ids = sorted(set(records(dataset_text(data_dir, prefix + "articles.tsv"))),
                 key=lambda s: s.encode("utf-8"))
    index = {name: i for i, name in enumerate(ids)}
    edges = {tuple(row.split("\t")) for row in records(dataset_text(data_dir, prefix + "links.tsv"))}
    out = [[] for _ in ids]
    for a, b in sorted(edges):
        out[index[a]].append(index[b])
    return ids, out


def wiki_topics(data_dir, ids):
    rows = [row.split("\t") for row in records(dataset_text(
        data_dir, "wikispeedia_paths-and-graph/categories.tsv"))]
    result = []
    for name in ["Science", "History", "Geography"]:
        prefix = "subject." + name
        selected = {article for article, label in rows
                    if label == prefix or label.startswith(prefix + ".")}
        result.append([float(article in selected) / len(selected) for article in ids])
    return result


def transition(out):
    """Ma trận cột cho oracle đồ thị nhỏ, độc lập vòng chia điểm của bài làm."""
    n = len(out)
    matrix = [[0.0] * n for _ in out]
    for j, targets in enumerate(out):
        destinations = sorted(set(targets)) or list(range(n))
        for i in destinations:
            matrix[i][j] = 1.0 / len(destinations)
    return matrix


def one_step(out, r, beta, v):
    matrix = transition(out)
    return [beta * math.fsum(a * b for a, b in zip(row, r)) + (1-beta)*v[i]
            for i, row in enumerate(matrix)]


def dense_solution(out, beta, v):
    """Giải hệ tuyến tính bằng khử Gauss có chọn pivot, không dùng power iteration."""
    matrix = transition(out)
    n = len(out)
    aug = [[float(i == j) - beta * matrix[i][j] for j in range(n)]
           + [(1-beta) * v[i]] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda i: abs(aug[i][col]))
        aug[col], aug[pivot] = aug[pivot], aug[col]
        scale = aug[col][col]
        require(abs(scale) > 1e-15, "Oracle gặp hệ suy biến")
        aug[col] = [x / scale for x in aug[col]]
        for i in range(n):
            if i != col:
                scale = aug[i][col]
                aug[i] = [x - scale*y for x, y in zip(aug[i], aug[col])]
    return [row[-1] for row in aug]


def incoming_operator(out, beta, v):
    n = len(out)
    incoming = [[] for _ in out]
    dangling = []
    for j, targets in enumerate(out):
        if not targets:
            dangling.append(j)
        for i in targets:
            incoming[i].append((j, 1.0 / len(targets)))
    def apply(r):
        missing = math.fsum(r[j] for j in dangling) / n
        return [beta * (math.fsum(r[j]*w for j, w in incoming[i]) + missing)
                + (1-beta)*v[i] for i in range(n)]
    return apply


def sparse_solution(out, beta, v):
    apply = incoming_operator(out, beta, v)
    r = [1.0 / len(out)] * len(out)
    for _ in range(5000):
        new = apply(r)
        if math.fsum(abs(a-b) for a, b in zip(new, r)) < 1e-14:
            return new
        r = new
    raise RuntimeError("Oracle thưa không hội tụ")


def reference_normalize(text):
    result = []
    space = False
    for char in text:
        if char in " \t\n\r\v\f":
            if result:
                space = True
        else:
            if space:
                result.append(" ")
            space = False
            result.append(chr(ord(char)+32) if "A" <= char <= "Z" else char)
    return "".join(result)


def reference_shingles(text, k):
    return set(text[i:i+k] for i in range(max(0, len(text)-k+1)))


def reference_id(text, p):
    # Đọc 8 ký tự hex tương ứng 4 byte đầu, khác cách đọc bytes trong lời giải.
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16) % p


def reference_signature(values, params):
    result = []
    for coefficients in params["hash_functions"]:
        candidates = [(coefficients["a"]*x + coefficients["b"]) % params["p"] for x in values]
        result.append(min(candidates) if candidates else params["p"])
    return result


def small_graphs():
    yield [[1], [0], []]
    yield [[]]
    yield [[], [], [], []]
    yield [[1], [2], [0], [3], []]
    rng = random.Random(20261104)
    for n in [3, 5, 7, 9]:
        yield [[j for j in range(n) if rng.random() < 0.23] for _ in range(n)]


def ids_for(out):
    return [f"node_{i}" for i in range(len(out))]


def test_a1(s, ctx):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        a, e = root / "articles.tsv", root / "links.tsv"
        a.write_text("# ids\nZ\nA\n孤\nC\nA\n\n", encoding="utf-8")
        e.write_text("# edges\nA\tZ\nZ\tZ\nA\tZ\n孤\tA\n", encoding="utf-8")
        names, out = s.load_graph(a, e)
        require(names == ["A", "C", "Z", "孤"], "Thứ tự/tập ID sai")
        require([sorted(x) for x in out] == [[2], [], [2], [0]], "Sai cạnh/nút cụt")
        e.write_text("A\tunknown\n")
        raises_value_error(s.load_graph, a, e)
        a.write_text("# empty\n"); e.write_text("")
        raises_value_error(s.load_graph, a, e)


def test_a2(s, ctx):
    for out in small_graphs():
        u = [1/len(out)] * len(out)
        for beta in [0.37, 0.85]:
            vector(s.pagerank(ids_for(out), out, beta, 1e-14, 1),
                   one_step(out, u, beta, u), 1e-12)


def test_a3(s, ctx):
    for out in small_graphs():
        u = [1/len(out)] * len(out)
        for beta in [0.61, 0.93]:
            vector(s.pagerank(ids_for(out), out, beta, 1e-12, 2000),
                   dense_solution(out, beta, u))
    ids, out = wiki_graph(ctx.data_dir)
    u = [1/len(ids)] * len(ids)
    actual = s.pagerank(ids, out, .85, 1e-10, 1000)
    vector(actual, sparse_solution(out, .85, u))
    vector(actual, incoming_operator(out, .85, u)(actual), 1e-9)


def test_a4(s, ctx):
    out = [[1, 2], [2], [], [0]]
    u = [0.25]*4
    expected = u
    for _ in range(3):
        expected = one_step(out, expected, .85, u)
    vector(s.pagerank(ids_for(out), out, .85, 1e-30, 3), expected, 1e-12)
    vector(s.pagerank(ids_for(out), out, .85, 2.0, 100),
           one_step(out, u, .85, u), 1e-12)
    actual = s.pagerank(ids_for(out), out, .85, 1e-10, 1000)
    close(sum(actual), 1.0, 1e-10)
    require(min(actual) >= -1e-12, "Điểm âm")
    for beta, tol, count in [(1,1e-10,3),(0,1e-10,3),(.85,0,3),(.85,1e-10,0)]:
        raises_value_error(s.pagerank, ids_for(out), out, beta, tol, count)
    # Đảo chỉ số đỉnh phải bảo toàn nghiệm sau khi ánh xạ ngược.
    order = [2, 0, 3, 1]
    inverse = {old: new for new, old in enumerate(order)}
    changed = [[inverse[j] for j in out[old]] for old in order]
    vector(s.pagerank(ids_for(changed), changed, .85, 1e-10, 1000),
           [actual[i] for i in order])


def test_b1(s, ctx):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "categories.tsv"
        path.write_text("# labels\nA\tsubject.Science\nA\tsubject.Science.Physics\n"
                        "B\tsubject.ScienceX\nC\tsubject.Science.Biology\n"
                        "D\tsubject.History\nA\tsubject.Science\n\n")
        vector(s.topic_distribution(list("ABCD"), path, "subject.Science"), [.5,0,.5,0], 1e-12)
        vector(s.topic_distribution(list("ABCD"), path, "subject.History"), [0,0,0,1], 1e-12)
        raises_value_error(s.topic_distribution, list("ABCD"), path, "subject.Unknown")
        path.write_text("Missing\tsubject.Science\n")
        raises_value_error(s.topic_distribution, list("ABCD"), path, "subject.Science")


def test_b2(s, ctx):
    for out in small_graphs():
        n = len(out)
        for v in [[0.0]*(n-1)+[1.0], [2*(i+1)/(n*(n+1)) for i in range(n)]]:
            vector(s.pagerank(ids_for(out), out, .85, 1e-14, 1, v),
                   one_step(out, v, .85, v), 1e-12)
    for v in [[1], [-.1, 1.1], [.2,.2], [float('nan'),1], [float('inf'),0]]:
        raises_value_error(s.pagerank, ['A','B'], [[1],[]], .85, 1e-10, 100, v)


def test_b3(s, ctx):
    for out in small_graphs():
        n = len(out)
        v = [0.]*(n-1)+[1.]
        vector(s.pagerank(ids_for(out), out, .85, 1e-12, 1000, v), dense_solution(out, .85, v))
    ids, out = wiki_graph(ctx.data_dir)
    for v in wiki_topics(ctx.data_dir, ids):
        actual = s.pagerank(ids, out, .85, 1e-10, 1000, v)
        vector(actual, sparse_solution(out, .85, v))
        vector(actual, incoming_operator(out, .85, v)(actual), 1e-9)


def test_b4(s, ctx):
    out = [[1], [0,2], [], [3]]
    vs = [[1.,0,0,0], [0,.5,.5,0], [0,0,0,1.]]
    rs = [dense_solution(out,.85,v) for v in vs]
    for weights in [[.5,.3,.2], [0.,1.,0.], [.1,.2,.7]]:
        mixed_v = [sum(w*v[i] for w,v in zip(weights,vs)) for i in range(4)]
        vector(s.mix_pageranks(rs,weights), dense_solution(out,.85,mixed_v))
    for scores, weights in [([],[]), ([[1],[1,0]],[.5,.5]), ([[1]],[.2]), ([[1]],[-1])]:
        raises_value_error(s.mix_pageranks, scores, weights)


def test_c1(s, ctx):
    texts = ['', ' \t\r\n\v\f', ' A\tB\n C ', 'ÁÉİß ABC\u00a0D\u2003E',
             'e\u0301 É\r\n🙂XYZ', 'abababa', 'short', '123456789']
    for text in texts:
        expected = reference_normalize(text)
        require(s.normalize_text(text) == expected, "Chuẩn hóa sai ASCII/Unicode/khoảng trắng")
        for k in [1,2,9,20]:
            require(s.shingles(expected,k) == reference_shingles(expected,k), "Tập shingle sai")
    for k in [0,-1,1.5]:
        raises_value_error(s.shingles, 'text', k)


def test_c2(s, ctx):
    for word in ['', 'abcdefghi', '🙂e\u0301ABC', 'Á B', '123456789']:
        for p in [5, 2147483647]:
            actual = s.shingle_id(word,p)
            require(isinstance(actual,numbers.Integral) and not isinstance(actual,bool), "Mã phải là số nguyên")
            require(actual == reference_id(word,p), "Sai SHA-256/byte order/modulo")
    params = {'p':5, 'hash_functions':[{'a':1,'b':1},{'a':3,'b':1}]}
    for values in [{0,3},{2},{1,3,4},{0,2,3}]:
        integers(s.minhash(values,params),reference_signature(values,params))
    params = json.loads(ctx.hash_params.read_text())
    values = {0,1,params['p']-1,params['p']//2,1987654321}
    integers(s.minhash(values,params),reference_signature(values,params))
    # Sáu bài lấy mẫu tất định từ toàn kho, không chỉ các ví dụ công khai.
    ids, _ = wiki_graph(ctx.data_dir)
    sample = random.Random(314159).sample(ids, min(6,len(ids)))
    for article in sample:
        text = dataset_text(ctx.data_dir,'plaintext_articles/'+article+'.txt')
        parts = reference_shingles(reference_normalize(text),params['shingle_length'])
        values = {reference_id(part,params['p']) for part in parts}
        integers(s.minhash(values,params),reference_signature(values,params))


def test_c3(s, ctx):
    for a,b in [(set(),set()), (set(),{'a'}), ({'a'},{'a'}), ({'a'},{'b'}),
                ({'a','b'},{'b','c'}), ({'a','b'},{'a','b','c'})]:
        expected = len(a&b)/len(a|b) if a|b else 1.0
        close(s.jaccard(a,b),expected)
    for a,b,ea,eb,expected in [([1,2],[1,3],False,False,.5),
                              ([1,2],[2,1],False,False,0.),
                              ([7,7],[7,7],True,True,1.),
                              ([7,7],[1,2],True,False,0.),
                              ([1,2,3],[1,2,3],False,False,1.)]:
        close(s.signature_similarity(a,b,ea,eb),expected)
    # Bộ cặp chính thức: dữ liệu văn bản và chữ ký tham chiếu được tạo độc lập.
    params = json.loads(ctx.hash_params.read_text())
    cache = {}
    for a, b in official_pairs(ctx.pairs):
        for article in (a, b):
            if article not in cache:
                text = dataset_text(ctx.data_dir, 'plaintext_articles/' + article + '.txt')
                parts = reference_shingles(reference_normalize(text), params['shingle_length'])
                codes = {reference_id(part, params['p']) for part in parts}
                cache[article] = (parts, reference_signature(codes, params))
        x, sx = cache[a]
        y, sy = cache[b]
        exact = len(x & y) / len(x | y) if x | y else 1.0
        estimated = (float(not x and not y) if not x or not y else
                     sum(i == j for i, j in zip(sx, sy)) / len(sx))
        close(s.jaccard(x.copy(), y.copy()), exact)
        close(s.signature_similarity(sx.copy(), sy.copy(), not x, not y), estimated)


def test_c4(s, ctx):
    params={'p':11,'hash_functions':[{'a':3,'b':2},{'a':7,'b':1},{'a':1,'b':0}]}
    integers(s.minhash(set(),params),[11,11,11])
    integers(s.minhash({9},params),reference_signature({9},params))
    a,b={1,3,5},{2,3,9}
    x,y=s.minhash(a,params),s.minhash(b,params)
    integers(x,reference_signature(a,params))
    integers(y,reference_signature(b,params))
    integers(s.minhash(a|b,params),[min(i,j) for i,j in zip(x,y)])
    require(a=={1,3,5} and b=={2,3,9}, "Hàm sửa tập đầu vào")
    raises_value_error(s.signature_similarity,[],[],True,True)
    raises_value_error(s.signature_similarity,[1],[1,2],False,False)


def run_process(command, timeout, cwd=None, new_session=True):
    """Giới hạn thời gian và kết thúc cả nhóm tiến trình khi timeout (POSIX)."""
    with tempfile.TemporaryFile(mode='w+b') as output:
        proc = subprocess.Popen(command, cwd=cwd, stdout=output, stderr=subprocess.STDOUT,
                                start_new_session=(os.name=='posix' and new_session))
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name=='posix' and new_session:
                os.killpg(proc.pid,signal.SIGKILL)
            else:
                proc.kill()
            proc.wait()
            raise TimeoutError(f"Vượt {timeout:g} giây")
        finally:
            # Worker sở hữu nhóm; dọn cả tiến trình con còn sót khi worker kết thúc.
            # CLI bên trong worker dùng cùng nhóm để timeout ngoài không bỏ sót nó.
            if os.name=='posix' and new_session:
                try:
                    os.killpg(proc.pid,signal.SIGKILL)
                except ProcessLookupError:
                    pass
        output.seek(0)
        message=output.read(8192).decode('utf-8',errors='replace')
    require(proc.returncode==0, f"Tiến trình thoát mã {proc.returncode}: {message[-2000:]}")
    return message


def read_csv(path,header):
    with path.open(encoding='utf-8',newline='') as handle:
        reader=csv.reader(handle)
        require(next(reader,None)==header,f"Header sai: {path.name}")
        rows=list(reader)
    require(all(len(row)==len(header) for row in rows),f"Sai số cột: {path.name}")
    return rows


def official_pairs(path):
    """Đọc đúng định dạng cặp; việc kiểm ID được thực hiện trước khi chấm."""
    rows = read_csv(path, ['article_id_a', 'article_id_b'])
    require(bool(rows), 'Danh sách cặp rỗng')
    return [tuple(row) for row in rows]


def test_io(s, ctx):
    # Kiểm tra CLI bằng đầu vào khác dữ liệu chính thức, bao gồm tập rỗng.
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        data=root/'input'; graph=data/'wikispeedia_paths-and-graph'
        texts=data/'plaintext_articles';graph.mkdir(parents=True);texts.mkdir()
        ids=['A','B','C','D','E']
        out=[[1,2],[0],[],[3],[]]
        graph.joinpath('articles.tsv').write_text('E\nD\nC\nB\nA\n')
        graph.joinpath('links.tsv').write_text('A\tB\nA\tC\nB\tA\nD\tD\nA\tB\n')
        graph.joinpath('categories.tsv').write_text('A\tsubject.Science.Physics\n'
            'B\tsubject.History\nC\tsubject.Geography\nD\tsubject.Geography.Countries\n')
        raw=['  The CAT sat\ton the MAT. ÁÉ🙂  ', 'the cat sat on a mat.', 'short', '', 'short']
        for name,text in zip(ids,raw):texts.joinpath(name+'.txt').write_text(text,encoding='utf-8')
        pairs=[('A','A'),('A','B'),('C','D'),('B','C'),('D','E')]
        pair_path=root/'pairs.csv'
        with pair_path.open('w',newline='') as f:
            writer=csv.writer(f);writer.writerow(['article_id_a','article_id_b']);writer.writerows(pairs)
        beta=.73
        params=json.loads(ctx.hash_params.read_text())
        expected_files={'pagerank.csv','topic_pagerank.csv','minhash.csv','similarities.csv'}
        for run in ['one','two']:
            target=root/run
            run_process([sys.executable,str(ctx.submission),'--data-dir',str(data),
                '--hash-params',str(ctx.hash_params),'--pairs',str(pair_path),
                '--output-dir',str(target),'--beta',str(beta),'--tol','1e-12',
                '--max-iter','1000'],ctx.timeout,cwd=root,new_session=False)
            require({p.name for p in target.iterdir()}==expected_files,'Không đúng bốn tệp đầu ra')
        for name in expected_files:
            require((root/'one'/name).read_bytes()==(root/'two'/name).read_bytes(),f"Không tái lập: {name}")
        target=root/'one'
        rows=read_csv(target/'pagerank.csv',['article_id','score'])
        require([r[0] for r in rows]==ids,'Thứ tự hoặc ID PageRank sai')
        vector([float(r[1]) for r in rows],dense_solution(out,beta,[.2]*5))
        vs=[[1,0,0,0,0],[0,1,0,0,0],[0,0,.5,.5,0]]
        rs=[dense_solution(out,beta,v) for v in vs]
        rs.append([sum(w*r[i] for w,r in zip([.5,.3,.2],rs)) for i in range(5)])
        rows=read_csv(target/'topic_pagerank.csv',['topic','article_id','score'])
        expected_keys=[(topic,name) for topic in ['Science','History','Geography','r_mix'] for name in ids]
        require([(r[0],r[1]) for r in rows]==expected_keys,'Sai nhóm/ID chủ đề')
        vector([float(r[2]) for r in rows],[x for r in rs for x in r])
        parts=[reference_shingles(reference_normalize(t),params['shingle_length']) for t in raw]
        signatures=[reference_signature({reference_id(t,params['p']) for t in row},params) for row in parts]
        rows=read_csv(target/'minhash.csv',['article_id','shingle_count']+
                      [f'h{i:03d}' for i in range(len(params['hash_functions']))])
        require([r[0] for r in rows]==ids,'Sai ID chữ ký')
        for row,part,sig in zip(rows,parts,signatures):
            require(int(row[1])==len(part),'Đếm shingle sai')
            integers([int(x) for x in row[2:]],sig)
        rows=read_csv(target/'similarities.csv',
                      ['article_id_a','article_id_b','jaccard_exact','jaccard_estimate'])
        require([(r[0],r[1]) for r in rows]==pairs,'Sai thứ tự cặp')
        for row,(a,b) in zip(rows,pairs):
            i,j=ids.index(a),ids.index(b);x,y=parts[i],parts[j]
            exact=len(x&y)/len(x|y) if x|y else 1.0
            estimated=(float(not x and not y) if not x or not y else
                       sum(a==b for a,b in zip(signatures[i],signatures[j]))/len(signatures[i]))
            close(float(row[2]),exact);close(float(row[3]),estimated)


TESTS=dict(zip([r[0] for r in RUBRIC],[test_a1,test_a2,test_a3,test_a4,test_b1,test_b2,
                                    test_b3,test_b4,test_c1,test_c2,test_c3,test_c4,test_io]))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('submission',type=Path)
    parser.add_argument('--data-dir',type=Path,default=ROOT/'data')
    parser.add_argument('--hash-params',type=Path,default=ROOT/'assignment/minhash_params.json')
    parser.add_argument('--pairs',type=Path,default=ROOT/'data/pairs.csv',
                        help='Bộ cặp Wikispeedia dùng để chấm độ tương đồng.')
    parser.add_argument('--timeout',type=float,default=180,help='Giây tối đa cho mỗi nhóm tiêu chí.')
    parser.add_argument('--report',type=Path,help='Ghi báo cáo chi tiết dạng JSON.')
    parser.add_argument('--worker',choices=TESTS,help=argparse.SUPPRESS)
    parser.add_argument('--worker-result',type=Path,help=argparse.SUPPRESS)
    args=parser.parse_args()
    args.submission=args.submission.resolve();args.data_dir=args.data_dir.resolve()
    args.hash_params=args.hash_params.resolve()
    args.pairs=args.pairs.resolve()
    if not args.submission.is_file():parser.error('Không tìm thấy tệp bài nộp')
    if not math.isfinite(args.timeout) or args.timeout<=0:parser.error('timeout phải dương và hữu hạn')
    if args.worker:
        result={'passed':False}
        try:
            # Không để print của bài làm trộn vào giao thức kết quả.
            with open(os.devnull,'w') as sink,contextlib.redirect_stdout(sink),contextlib.redirect_stderr(sink):
                module=import_submission(args.submission)
                TESTS[args.worker](module,args)
            result={'passed':True}
        except BaseException as error:
            result={'passed':False,'error':f'{type(error).__name__}: {error}',
                    'traceback':traceback.format_exc(limit=5)}
        args.worker_result.write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
        return
    # Thiếu dữ liệu là lỗi cấu hình của người chấm, không phải lỗi bài nộp.
    try:
        ids,out=wiki_graph(args.data_dir)
        require(len(ids)==4604 and sum(map(len,out))==119882,'Không đúng phiên bản Wikispeedia')
        params=json.loads(args.hash_params.read_text())
        require(params['p']==2147483647 and len(params['hash_functions'])==128,
                'Không đúng bộ hàm băm chính thức')
        dataset_text(args.data_dir,'plaintext_articles/'+ids[0]+'.txt')
        pairs = official_pairs(args.pairs)
        known = set(ids)
        require(all(a in known and b in known for a, b in pairs),
                'Bộ cặp chứa ID ngoài Wikispeedia')
        require(len({tuple(sorted(pair)) for pair in pairs}) == len(pairs),
                'Bộ cặp có cặp trùng hoặc đảo chiều')
    except Exception as error:
        parser.error(f'Dữ liệu chấm chưa sẵn sàng: {error}')
    results=[]
    with tempfile.TemporaryDirectory(prefix='wikispeedia-grader-') as tmp:
        for code,points,title in RUBRIC:
            output=Path(tmp)/(code+'.json')
            command=[sys.executable,str(Path(__file__).resolve()),str(args.submission),
                '--data-dir',str(args.data_dir),'--hash-params',str(args.hash_params),
                '--pairs',str(args.pairs),
                '--timeout',str(args.timeout),'--worker',code,'--worker-result',str(output)]
            try:
                run_process(command,args.timeout)
                result=json.loads(output.read_text(encoding='utf-8'))
            except Exception as error:
                result={'passed':False,'error':f'{type(error).__name__}: {error}'}
            score=points if result.get('passed') is True else 0
            row={'criterion':code,'description':title,'score':score,'max_score':points,**result}
            results.append(row)
            print(f'{code:>2}  {score:2}/{points:<2}  {title}',flush=True)
            if not result.get('passed'):print('    '+result.get('error','Không có kết quả'),flush=True)
    report={'submission':str(args.submission),'score':sum(r['score'] for r in results),
            'max_score':100,'criteria':results,
            'pairs_file':str(args.pairs),'pairs_count':len(pairs),
            'coverage':'PageRank toàn bộ Wikispeedia; MinHash 6 bài lấy mẫu tất định và fixture; độ tương đồng trên mọi cặp chính thức; main chạy hai lần trên dữ liệu nhỏ.'}
    print(f"TỔNG: {report['score']}/100",flush=True)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
