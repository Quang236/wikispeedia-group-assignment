# Bài tập: PageRank, PageRank theo chủ đề và chữ ký MinHash

## 1. Mục tiêu và dữ liệu

Sinh viên tự cài đặt ba thuật toán trên bộ dữ liệu Wikispeedia. Bài làm phải chạy lại được trên cả dữ liệu đã công bố và dữ liệu kiểm thử khác có cùng định dạng. Nộp mã nguồn và kết quả; chỉ nộp bảng kết quả không đủ để chấm tính tổng quát của thuật toán.

Tài liệu học:

- [Bài 03 — PageRank](https://courses.iaidev.com/ds-foundation-algorithms/2627-1/lecture-03-pagerank-mo-hinh-va-tinh-toan.html).
- [Bài 04 — PageRank theo chủ đề](https://courses.iaidev.com/ds-foundation-algorithms/2627-1/lecture-04-pagerank-theo-chu-de-lien-ket-rac-va-hits.html).
- [Bài 05 — Shingling và MinHash](https://courses.iaidev.com/ds-foundation-algorithms/2627-1/lecture-05-bieu-dien-tuong-dong-shingling-va-minhash.html).

Các quy tắc tiền xử lý, tham số, định dạng và thang điểm bên dưới là đặc tả đề xuất riêng cho bài tập này.

Dữ liệu nằm trong `data/`:

| Tệp | Kích thước (byte) | SHA-256 |
|---|---:|---|
| `wikispeedia_paths-and-graph.tar.gz` | 9901821 | `97697096f5d2dcb77aa69e3992305c6c561de89edb9fb10b5ad9feaf8ba534d5` |
| `wikispeedia_articles_plaintext.tar.gz` | 35844149 | `8e43d12822d05746a59f7de8987ffd6eafa57d248303d1c02cfe85b519359dc1` |

Sử dụng `articles.tsv`, `links.tsv`, `categories.tsv` và các tệp `plaintext_articles/*.txt`.

Quy ước đọc đồ thị:

1. Bỏ dòng trống và dòng bắt đầu bằng `#` trong ba tệp TSV.
2. Tập đỉnh lấy từ `articles.tsv`, bao gồm cả trang không xuất hiện trong danh sách cạnh.
3. Giữ nguyên ID mã hóa phần trăm, không giải mã URL. Sắp ID theo thứ tự từ điển của byte UTF-8; đây là thứ tự vector và các hàng đầu ra.
4. Mỗi dòng `links.tsv` là `source<TAB>target`; cạnh có hướng. Gộp cạnh trùng, giữ cạnh tự nối. Báo lỗi nếu đầu mút không có trong tập đỉnh.
5. Đối chiếu ID bài viết với tên tệp văn bản, bỏ phần mở rộng `.txt`. Thiếu tệp là lỗi đầu vào, không được coi là văn bản rỗng.

Đã kiểm tra trực tiếp hai tệp dữ liệu: **4604 đỉnh, 119882 cạnh phân biệt, 17 nút cụt, 110 cạnh tự nối và 4604 tệp văn bản**. Đây là số kiểm tra dữ liệu, không phải hằng số được phép gắn cứng trong thuật toán.

## 2. Phần A — Tính PageRank toàn cục (30 điểm)

Cho đồ thị có hướng, tự cài đặt power iteration để tính điểm của mọi đỉnh. Dùng danh sách kề hoặc ma trận thưa; không dựng ma trận Google đặc.

Đặt $n$ là số đỉnh, $d_j$ là bậc ra, $u_i = 1/n$, và $\delta_t$ là tổng điểm ở các nút có bậc ra bằng 0. Cập nhật đồng thời:

$$
r_i^{t+1}=\beta\sum_{j\to i}\frac{r_j^t}{d_j}
             +\beta\delta_t\frac1n+(1-\beta)\frac1n.
$$

Trong tổng chỉ có nguồn với bậc ra dương. Mọi đóng góp trong một vòng lấy từ vector cũ.

Tham số chính thức: $\beta = 0.85$, $\mathrm{tol} = 10^{-10}$, $\mathrm{max\_iter} = 1000$, số thực 64 bit, $r^0 = u$. Dừng sau khi hoàn tất một vòng và $\lVert r^{t+1}-r^t\rVert_1 \le \mathrm{tol}$; trả vector mới. Không chuẩn hóa lại cuối mỗi vòng để che lỗi mất khối lượng.

Đầu ra duy nhất của phần A là **`pagerank.csv`**, có header `article_id,score`, chứa điểm của toàn bộ đỉnh, mỗi đỉnh một dòng theo thứ tự ID đã quy định. Bộ chấm tự tính tổng điểm, sai số so với nghiệm tham chiếu và sai số dư từ tệp này.

Thuật toán phải nhận tham số đầu vào; bộ chấm có thể thay $\beta$, `tol`, `max_iter` và đồ thị. Nếu hết số vòng mà chưa đạt ngưỡng, trả vector hiện tại. Phần A không yêu cầu xuất thống kê hội tụ hoặc danh sách top trang.

## 3. Phần B — Tính PageRank theo chủ đề (30 điểm)

Tạo ba tập chủ đề từ `categories.tsv`:

| Tên chủ đề | Tiền tố phân cấp | Số trang phân biệt trong dữ liệu chính thức |
|---|---|---:|
| Science | `subject.Science` | 1105 |
| History | `subject.History` | 525 |
| Geography | `subject.Geography` | 1063 |

Một nhãn thuộc chủ đề khi bằng đúng tiền tố hoặc bắt đầu bằng `tiền_tố + "."`. Một bài viết có thể thuộc nhiều chủ đề; trong mỗi tập chỉ được tính một lần. Không phân loại lại bằng từ khóa trong văn bản.

Với tập chủ đề không rỗng $S$, đặt $v_i = 1/\lvert S\rvert$ nếu $i$ thuộc $S$, ngược lại bằng 0. Khởi tạo $r^0 = v$, giữ nguyên toàn bộ đồ thị và tính:

$$
r_i^{t+1}=\beta\sum_{j\to i}\frac{r_j^t}{d_j}
             +\beta\delta_t\frac1n+(1-\beta)v_i.
$$

**Bù nút cụt luôn theo phân phối đều $u$, không theo $v$.** Đây là quy ước của Bài 04. Trang ngoài tập chủ đề vẫn được truyền điểm. Dùng cùng tham số dừng như phần A.

Đầu ra duy nhất của phần B là **`topic_pagerank.csv`**, có header `topic,article_id,score`, chứa cả ba vector chủ đề và vector ghép:

1. Tính điểm cho Science, History và Geography.
2. Ghép $r_{\mathrm{mix}} = 0.5r_{\mathrm{Science}} + 0.3r_{\mathrm{History}} + 0.2r_{\mathrm{Geography}}$.
3. Ghi bốn nhóm dòng với giá trị cột `topic` lần lượt là `Science`, `History`, `Geography`, `r_mix`. Mỗi nhóm chứa đủ mọi đỉnh theo thứ tự ID chung; mỗi cặp `(topic,article_id)` xuất hiện đúng một lần. Với dữ liệu chính thức, tệp có **18416 dòng dữ liệu**, không tính header.

Bộ chấm tự tính nghiệm tham chiếu với $v_{\mathrm{mix}} = 0.5v_{\mathrm{Science}} + 0.3v_{\mathrm{History}} + 0.2v_{\mathrm{Geography}}$, rồi đối chiếu với nhóm `r_mix` trong CSV. Sinh viên chỉ cần xuất tệp trên, không phải nộp thống kê hội tụ hoặc báo cáo sai khác riêng. Nếu hết số vòng mà chưa đạt ngưỡng, trả vector hiện tại như phần A.

Hàm tính lõi phải nhận được một phân phối $v$ bất kỳ hợp lệ, không chỉ ba chủ đề trên. Báo lỗi rõ ràng nếu tập chủ đề rỗng hoặc $v$ sai kích thước, có số không hữu hạn, có giá trị âm hay tổng lệch 1 quá $10^{-12}$.

## 4. Phần C — Tính MinHash signature (35 điểm)

### 4.1. Chuẩn hóa và tạo tập shingle

Đọc toàn bộ mỗi tệp bằng UTF-8, báo lỗi nếu mã hóa không hợp lệ. Để tránh khác nhau do thư viện tách từ, áp dụng chính xác thứ tự sau:

1. Chỉ đổi các chữ ASCII `A`–`Z` thành `a`–`z`; giữ nguyên mọi ký tự khác, không bỏ dấu, không chuẩn hóa Unicode.
2. Thay mỗi dãy liên tiếp thuộc tập `U+0020`, `\t`, `\n`, `\r`, `\v`, `\f` bằng một dấu cách ASCII; bỏ dấu cách ASCII ở hai đầu.
3. Giữ dấu câu, tiêu đề, nội dung bảng và phần đầu/cuối tệp. Không tự xóa nội dung phụ vì đây là một lựa chọn tiền xử lý riêng cần đặc tả khác.
4. Lấy tập các cửa sổ **9 ký tự Unicode liên tiếp**, tính theo code point, không theo byte hay từ. Loại shingle trùng. Nếu chuỗi ngắn hơn 9, tập shingle rỗng.

Hàm tạo shingle phải nhận $k$ để chấm các ví dụ nhỏ; chạy chính thức dùng $k = 9$.

### 4.2. Mã shingle và hàm băm dùng chung

Đề cung cấp `assignment/minhash_params.json` với $p = 2147483647$ và 128 cặp hệ số $(a_j,b_j)$ có thứ tự. Sinh viên dùng nguyên bộ hệ số cho mọi tài liệu, không tự lấy mẫu và không dùng `hash()` mặc định của ngôn ngữ.

Với shingle $s$, tính SHA-256 của byte UTF-8, lấy **4 byte đầu**, đọc thành số nguyên không dấu big-endian, rồi lấy modulo $p$; kết quả là $x(s)$.

$$
h_j(x)=(a_jx+b_j)\bmod p,
\qquad \sigma_j(D)=\min_{s\in S_9(D)}h_j(x(s)),\quad j=0,\ldots,127.
$$

Lưu **giá trị băm nhỏ nhất**, không lưu shingle đạt min. Phép nhân và cộng phải thực hiện đúng bằng số nguyên; số nguyên 64 bit có dấu đủ cho miền giá trị đã chọn. Không dùng số thực 64 bit để tính modulo.

Tập rỗng nhận vector gồm 128 giá trị $p$, là giá trị đánh dấu lớn hơn mọi giá trị băm hợp lệ. Giá trị đánh dấu không phải kết quả băm thực.

Xuất `minhash.csv`: `article_id,shingle_count,h000,...,h127`. `shingle_count` đếm các chuỗi shingle phân biệt trước bước băm, không đếm mã băm. Các giá trị chữ ký phải là số nguyên thập phân.

### 4.3. Ước lượng tương đồng

Với **100 cặp Wikispeedia chính thức** trong [data/pairs.csv](data/pairs.csv), xuất `similarities.csv`: `article_id_a,article_id_b,jaccard_exact,jaccard_estimate`. Mỗi dòng đầu vào tương ứng đúng một dòng đầu ra, giữ nguyên thứ tự và ID; kết quả có 100 dòng dữ liệu, không tính header.

| Nhóm cặp | Số cặp | Mục đích |
|---|---:|---|
| Một bài với chính nó | 10 | Kiểm tra độ tương đồng bằng 1 |
| Hai bài khác nhau có Jaccard cao trong tập ứng viên đã khảo sát | 30 | Quan sát khả năng nhận diện nội dung tương đồng |
| Hai bài có chung một nhãn chủ đề | 30 | So sánh liên hệ chủ đề với mức trùng văn bản |
| Hai bài lấy mẫu ngẫu nhiên, không chung nhãn chủ đề cấp cao nhất | 30 | Bổ sung các cặp ít liên quan |

Các cặp được chọn cố định, không lặp cặp đảo chiều; mọi ID đều có trong `articles.tsv` và có tệp văn bản tương ứng. Nhãn cùng chủ đề không bảo đảm Jaccard cao. Bộ cặp được dùng chung cho bài nộp và phần tự chấm độ tương đồng; không tự chọn lại cặp. Tệp [pairs_sample.csv](assignment/pairs_sample.csv) gồm 4 cặp trước đây chỉ còn dùng để chạy thử riêng.

- Jaccard chính xác tính trên **tập chuỗi shingle**, trước bước băm.
- Khi hai tập không rỗng, ước lượng là số tọa độ chữ ký bằng nhau chia cho 128; không lấy Jaccard của tập giá trị trong chữ ký.
- Quy ước riêng của bài tập: hai tập rỗng có cả hai độ tương đồng bằng 1; chỉ một tập rỗng thì cả hai bằng 0.
- Không cần so sánh mọi cặp trong kho và không yêu cầu LSH.

Các hàm băm affine là cách mô phỏng thực hành; không mặc nhiên thỏa giả thiết chọn đều tất cả hoán vị. Do đó, không dùng một ngưỡng sai số với Jaccard cho từng cặp để quyết định chữ ký tính đúng hay sai. Phần chất lượng xấp xỉ có thể báo MAE trên bộ cặp cố định như kết quả quan sát.

## 5. Dùng template, tự chấm và nộp bài

### 5.1. Chuẩn bị và hoàn thiện template

Sử dụng [submission_template.py](assignment/submission_template.py), yêu cầu Python 3.10 trở lên. Sao chép thành `submission.py` ở thư mục gốc bài tập và hoàn thiện các hàm có dấu `TODO`. Mỗi hàm đã có docstring mô tả đầu vào, đầu ra, quy ước xử lý và trường hợp biên. Giữ nguyên tên hàm, tham số và kiểu đầu ra; có thể thêm hàm phụ trong cùng tệp.

Mẫu đã viết sẵn `main()` để đọc tham số, gọi các hàm và ghi CSV. Cuối tệp có:

```python
if __name__ == "__main__":
    main()
```

Các hàm cần làm hiện báo `NotImplementedError`. Sau khi hoàn thiện chúng, chạy tệp sẽ tạo đủ đầu ra; import tệp để chấm từng hàm không tự chạy `main()`.

**Chuẩn bị dữ liệu và tệp bài làm.** Chạy các lệnh sau từ thư mục gốc chứa `data/` và `assignment/`:

```bash
cp assignment/submission_template.py submission.py
tar -xzf data/wikispeedia_paths-and-graph.tar.gz -C data
tar -xzf data/wikispeedia_articles_plaintext.tar.gz -C data
```

Chỉ sao chép mẫu lần đầu; các lần sau sửa tiếp `submission.py`. Sau khi giải nén, `data/` có hai thư mục `wikispeedia_paths-and-graph/` và `plaintext_articles/`. Giữ bộ hệ số [minhash_params.json](assignment/minhash_params.json) do đề cung cấp.

Nên hoàn thiện theo thứ tự: đọc đồ thị và PageRank; phân phối chủ đề và ghép vector; chuẩn hóa, shingle, mã băm, MinHash và độ tương đồng. Có thể tự chấm ngay khi mới làm xong một số hàm; không cần đợi hoàn thiện toàn bộ bài.

### 5.2. Chạy bài làm để tạo kết quả

Sau khi cài đặt các hàm, chạy từ thư mục gốc bài tập:

```bash
python3 submission.py
```

Lệnh mặc định dùng dữ liệu trong `data/`, bộ hệ số trong `assignment/minhash_params.json` và 100 cặp chính thức trong [data/pairs.csv](data/pairs.csv). Tệp cặp được cung cấp riêng cùng đề, không nằm trong hai tệp nén Wikispeedia. Kết quả được ghi vào `output/`:

| Tệp kết quả | Nội dung |
|---|---|
| `pagerank.csv` | Điểm PageRank của mọi trang |
| `topic_pagerank.csv` | Điểm theo Science, History, Geography và `r_mix` |
| `minhash.csv` | Số shingle phân biệt và chữ ký của mọi trang |
| `similarities.csv` | Jaccard chính xác và ước lượng trên 100 cặp chính thức |

Để chỉ rõ tệp cặp chính thức khi chạy:

```bash
python3 submission.py --pairs data/pairs.csv --output-dir output
```

Tệp cặp là CSV UTF-8, có header `article_id_a,article_id_b`, mỗi dòng là hai ID bài viết. `similarities.csv` giữ thứ tự các cặp trong đầu vào. Khi dùng `--data-dir data/extracted`, đường dẫn mặc định của bộ cặp vẫn là `data/pairs.csv`; dùng `--pairs` nếu chuyển tệp cặp sang nơi khác.

Dùng `python3 submission.py --help` để xem các tùy chọn `--data-dir`, `--output-dir`, `--hash-params`, `--pairs`, `--beta`, `--tol`, `--max-iter`. Bộ chấm có thể thay các đầu vào này hoặc import `submission.py` để gọi riêng từng hàm. Không gắn cứng đường dẫn, kích thước dữ liệu hoặc kết quả trong các hàm.

Nếu dữ liệu đã được giải nén vào `data/extracted/`, không cần giải nén lại; chạy:

```bash
python3 submission.py --data-dir data/extracted --output-dir output
```

### 5.3. Tự chấm và sửa bài

Dùng [autograder.py](autograder.py) được cung cấp cùng đề. Từ thư mục gốc bài tập, chạy:

```bash
python3 autograder.py submission.py --report grading_reports/self_check.json
```

Bộ chấm tự tìm dữ liệu trong `data/` hoặc `data/extracted/`; nếu chưa giải nén, bộ chấm có thể đọc trực tiếp hai tệp `.tar.gz`. Bộ chấm dùng `data/pairs.csv` cho phần độ tương đồng và nhận tùy chọn `--pairs` để thay đường dẫn. Bản thân `submission.py` vẫn cần dữ liệu đã giải nén khi chạy để xuất kết quả như mục 5.2. Bộ tự chấm không cần các tệp lời giải mẫu.

Kết quả trên màn hình hiển thị điểm từng nhóm `A1`–`A4`, `B1`–`B4`, `C1`–`C4`, `IO` và tổng điểm trên 100. Các nhóm tương ứng theo thứ tự với 13 dòng tiêu chí ở bảng điểm. Trong mỗi nhóm, qua tất cả ca kiểm thử thì nhận đủ điểm; một ca sai thì nhóm nhận 0. Các nhóm khác vẫn tiếp tục được chấm.

Đọc kết quả và sửa bài theo quy trình:

1. Tìm nhóm chưa đạt và thông báo lỗi ngay dưới nhóm đó. `NotImplementedError` nghĩa là còn hàm chưa cài đặt; `AssertionError` mô tả giá trị hoặc định dạng chưa đúng; `TimeoutError` nghĩa là nhóm chạy quá thời gian cho phép.
2. Mở `grading_reports/self_check.json` nếu cần chi tiết. `score` và `max_score` ở cấp ngoài là điểm tổng; danh sách `criteria` ghi điểm từng nhóm, `error` mô tả lỗi và `traceback` chỉ vị trí lỗi khi có.
3. Sửa các hàm liên quan trong `submission.py`, rồi chạy lại lệnh tự chấm. Hàm chưa làm không ngăn bộ chấm đánh giá độc lập những hàm đã hoàn thiện.
4. Khi đã hoàn thiện, chạy lại `submission.py` để tạo bốn CSV mới nhất cho bài nộp.

Bộ tự chấm gọi trực tiếp các hàm, trong đó nhóm C3 kiểm độ tương đồng trên toàn bộ 100 cặp chính thức bằng các tập shingle và chữ ký tham chiếu độc lập. Nhóm IO tự chạy `main()` trên dữ liệu nhỏ và các cặp riêng trong thư mục tạm để kiểm định dạng và đường xuất kết quả. Bộ chấm không lấy các CSV có sẵn trong `output/` để tính điểm và không thay thế bước tạo kết quả nộp bài.

Mỗi nhóm có thời gian tối đa mặc định 180 giây. Nếu cần thử trên máy chậm hơn hoặc dùng thư mục dữ liệu khác:

```bash
python3 autograder.py submission.py --data-dir data/extracted --timeout 300 --report grading_reports/self_check.json
```

Giới hạn thời gian tự chọn chỉ áp dụng cho lần chạy trên máy cá nhân; khi chấm chính thức dùng giới hạn do giảng viên công bố. Dùng `python3 autograder.py --help` để xem tùy chọn. Nếu nhận lỗi “Dữ liệu chấm chưa sẵn sàng”, kiểm tra đường dẫn dữ liệu và bộ hệ số trước khi sửa thuật toán.

Điểm tự chấm phản ánh bộ kiểm thử đi kèm: PageRank trên toàn đồ thị Wikispeedia, MinHash trên các bài lấy mẫu và dữ liệu nhỏ, độ tương đồng trên 100 cặp chính thức, cùng kiểm tra đầu ra. Giảng viên có thể dùng dữ liệu kiểm thử khác trong cùng đặc tả; không gắn cứng kết quả theo các ví dụ hoặc dữ liệu kiểm thử.

### 5.4. Nội dung bài nộp

**Bài nộp gồm một tệp mã nguồn `submission.py` và bốn CSV kết quả.** Nếu dùng thêm thư viện, ghi tên và phiên bản trong docstring đầu tệp; không tách lời giải sang các tệp Python khác. Cho phép NumPy/SciPy để lưu trữ và thao tác số, nhưng phải tự cài đặt PageRank, tạo shingle và MinHash; không gọi thuật toán hoàn chỉnh có sẵn.

Giữ định dạng đầu ra mà `main()` cung cấp: CSV UTF-8 có header, dùng dấu chấm thập phân, không có chỉ số dòng phụ; điểm số ghi 17 chữ số có nghĩa. Không làm tròn điểm trong các hàm tính toán. Chạy lại với cùng đầu vào phải cho cùng kết quả.

## 6. Bảng điểm

| Phần | Tiêu chí | Điểm |
|---|---|---:|
| A | Đọc đồ thị: đủ đỉnh, đúng hướng, gộp cạnh trùng, giữ cạnh tự nối | 5 |
| A | Một vòng cập nhật đúng, có cả nút cụt | 8 |
| A | Vector hội tụ khớp nghiệm tham chiếu trên đồ thị nhỏ và Wikispeedia | 12 |
| A | Vector đầu ra đúng quy tắc dừng và thỏa bất biến xác suất | 5 |
| B | Tập chủ đề và phân phối $v$ đúng, xử lý nhãn trùng | 6 |
| B | Cập nhật đúng với $v$ không đều, bù nút cụt theo $u$ | 10 |
| B | Vector nghiệm cho ba chủ đề khớp tham chiếu | 9 |
| B | Ghép chủ đề đúng, khớp nghiệm chạy từ $v_{\mathrm{mix}}$ | 5 |
| C | Chuẩn hóa và tập shingle đúng | 8 |
| C | Mã shingle, hàm băm và chữ ký khớp từng số nguyên | 17 |
| C | Jaccard và tỷ lệ tọa độ trùng đúng | 6 |
| C | Tập rỗng, tập một phần tử và các tính chất phép min đúng | 4 |
| Chung | Chạy lại được, đúng định dạng, kết quả ổn định và đủ đầu ra | 5 |
| **Tổng** | | **100** |
