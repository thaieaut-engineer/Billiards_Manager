# Quản lý quán Bi-a

Ứng dụng desktop quản lý bàn, phiên chơi, dịch vụ, hóa đơn và doanh thu — **Python 3.10+**, **PyQt6**, **SQLite** (MVC).

## Yêu cầu

- Python 3.10 trở lên  
- Windows / Linux / macOS (giao diện Qt)

## Cài đặt

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

## Chạy

```bash
python main.py
```

Lần đầu chạy, file cơ sở dữ liệu được tạo tại `data/billiard.db` (thư mục `data/` đã có trong repo; file `.db` bị `.gitignore`).

## Cấu trúc thư mục

| Đường dẫn | Mô tả |
|-----------|--------|
| `main.py` | Điểm vào ứng dụng |
| `app/controllers/` | Điều khiển, nối UI với model |
| `app/models/` | Truy vấn SQLite |
| `app/views/` | Nạp `app/ui/main_window.ui` |
| `app/ui/` | File Qt Designer (`.ui`) |
| `app/widgets/` | Widget tùy chỉnh (ví dụ ô bàn) |
| `app/database/` | Kết nối DB, schema |
| `data/` | Chứa `billiard.db` khi chạy (không commit file `.db`) |

## Ghi chú khi đưa lên GitHub

- **Không** commit `.venv/`, `__pycache__/`, và `data/*.db` (đã cấu hình trong `.gitignore`).
- **PyQt6** phát hành theo giấy phép riêng (GPL / thương mại tùy cách phân phối). Nếu công khai repo học tập thì thường ổn; nếu phân phối sản phẩm thương mại, nên xem lại điều khoản tại [riverbankcomputing.com](https://www.riverbankcomputing.com/software/pyqt/).
- Nếu trước đó đã lỡ commit `billiard.db`, cần gỡ khỏi lịch sử Git hoặc xóa file đó khỏi commit và chỉ giữ `.gitignore`.

## Phát triển

Giao diện chỉnh trong Qt Designer: mở `app/ui/main_window.ui`, sau đó chạy lại app để kiểm tra.
