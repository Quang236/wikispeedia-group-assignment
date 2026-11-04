# Wikispeedia — Dự án nhóm 3 người

Đây là bộ khởi đầu được tách từ **template chính thức** của giảng viên.
Chưa có thuật toán nào được giải hộ: các hàm còn `TODO` và `NotImplementedError`.
Tham khảo đề gốc `bai-tap-wikispeedia.md` trước khi lập trình.

## Cấu trúc và phân công

| File | Thành viên | Các hàm cần hoàn thành |
|---|---|---|
| `parts/person1.py` | Người 1 | `load_graph`, `pagerank`, `normalize_text`, `shingles` |
| `parts/person2.py` | Người 2 | `topic_distribution`, `mix_pageranks`, `jaccard`, `signature_similarity` |
| `parts/person3.py` | Người 3 | `shingle_id`, `minhash`; phụ trách ghép code, chạy grader, CSV |

**QUAN TRỌNG:** Chỉ điền nội dung vào hàm được giao; **không đổi tên, chữ ký hàm,
kiểu trả về**. Các docstring lấy nguyên văn từ template chính thức. Có thể thêm
`import` và `def` hàm phụ ở cấp module, nhưng không đặt lệnh chạy thử ở cấp module.

## Chuẩn bị Python và dữ liệu (cho mỗi thành viên)

Yêu cầu Python >= 3.10. Repo không kèm 45 MB dữ liệu nén và dữ liệu giải nén.
Lấy hai file `.tar.gz` từ **gói ZIP đề bài gốc** mà giảng viên đã phát, đặt vào `data/`:

- `data/wikispeedia_paths-and-graph.tar.gz`
- `data/wikispeedia_articles_plaintext.tar.gz`

Lệnh giải nén trên macOS/Linux:

```bash
tar -xzf data/wikispeedia_paths-and-graph.tar.gz -C data
tar -xzf data/wikispeedia_articles_plaintext.tar.gz -C data
```

`data/pairs.csv`, `assignment/minhash_params.json`, `autograder.py` và đề gốc
đã nằm sẵn trong repo starter. Không sửa bộ cặp/hệ số/đề.

## Ghép code (do người 3 phụ trách)

Ở thư mục dự án:

```bash
python3 build_submission.py
python3 autograder.py submission.py --report grading_reports/self_check.json
python3 submission.py
```

Script `build_submission.py` tự động lấy **đúng 10 hàm** từ 3 file trong `parts/`,
đưa vào `submission.py`, giữ nguyên `main()` của giảng viên và thu thập các
`import`/hàm phụ. Việc chạy script sẽ **ghi đè submission.py** — vì vậy KHÔNG
sửa trực tiếp `submission.py`. Mọi sửa đổi đều thực hiện trong `parts/*.py`.

Khi tất cả TODO được hoàn thiện, `python3 submission.py` tạo 4 file trong `output/`:
`pagerank.csv`, `topic_pagerank.csv`, `minhash.csv`, `similarities.csv`.

## Cách làm chung trên GitHub (repository PRIVATE)

**Một lần, người quản lý repository:**

1. Tạo repo **private** tên `wikispeedia-group-assignment` tại https://github.com/new
   (KHÔNG tích chọn tạo README/.gitignore vì bộ này đã có).
2. Giải nén starter ZIP, mở Terminal bên trong thư mục `wikispeedia-team-starter`.
3. Chạy lệnh dưới đây (thay `USERNAME` bằng tên GitHub của người tạo repo):

```bash
git init -b main
git add .
git commit -m "Initialize Wikispeedia group project"
git remote add origin https://github.com/USERNAME/wikispeedia-group-assignment.git
git push -u origin main
```

**Mời các thành viên:** GitHub repo → Settings → Collaborators → Add people.
Không công khai bài đang làm, không đưa token/mật khẩu lên repo.

**Mỗi người làm trên nhánh riêng:**

```bash
git clone https://github.com/USERNAME/wikispeedia-group-assignment.git
cd wikispeedia-group-assignment
git switch -c person1    # đổi thành person2/person3 tùy thành viên
# mở parts/person1.py để viết phần của mình
git add parts/person1.py
git commit -m "Implement person 1 tasks"
git push -u origin person1
```

Trên GitHub chọn `Compare & pull request` → tạo PR vào `main` → thành viên
khác kiểm tra → merge PR. Các nhánh chỉ sửa file riêng nên ít xung đột.

**Sau khi merge cả 3 PR**: người 3 `git pull`, `python3 build_submission.py`,
chạy autograder, kiểm tra kết quả và commit `submission.py`:

```bash
git add submission.py
git commit -m "Build integrated submission"
git push
```

`output/` được ignore để không commit CSV khi chưa hoàn tất; khi nộp thì gửi
`submission.py` và 4 CSV theo đúng yêu cầu giảng viên. Nếu cần thêm CSV vào repo,
chỉ thực hiện sau khi kiểm tra kỹ và thống nhất cả nhóm.

## Thứ tự review kiến thức

- Người 2 review PageRank của người 1 (dangling, teleport, L1).
- Người 3 review Topic PageRank & Jaccard của người 2 (prefix, trọng số, tập rỗng).
- Người 1 review MinHash của người 3 (SHA-256, integer modulo, empty signature).
- Sau khi ghép, cả 3 cùng giải thích được các thuật toán và đọc kết quả grader.

## Chấm thử

Tệp `submission.py` ban đầu còn `NotImplementedError`, nên khi chưa làm
các hàm, điểm grader thấp hoặc 0/100 là điều **đúng**, không phải lỗi script ghép.
Đừng ghi đè template gốc `assignment/submission_template.py`.
