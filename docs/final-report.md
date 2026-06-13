# Completion Report

## Status

- Python target: 3.12+
- Package wheel build: passed
- Automated tests: 37 passed
- Branch-aware coverage: 86.41%
- Pylint: 10.00/10
- Black: passed
- CLI smoke test: passed
- Tkinter GUI import smoke test: passed

## Architecture

Ứng dụng dùng Clean Architecture theo hướng UI -> application service ->
downloader protocol/factory -> infrastructure adapter. Domain models và
exception không phụ thuộc CLI, GUI hoặc dictionary nội bộ của `yt-dlp`.

Mỗi nền tảng có downloader class riêng để đăng ký bằng factory. Hiện các class
dùng chung engine `YtDlpDownloader`; adapter mới có thể thay engine mà không đổi
service hoặc UI.

## Libraries

- `yt-dlp`: extractor, playlist, format selection, retries, resume và progress.
- `Typer`: CLI typed command/subcommand.
- `Rich`: bảng metadata và progress bar.
- `Pydantic`: validation config và domain models.
- `PyYAML`: đọc `config.yaml`.
- `pytest`/`pytest-cov`: unit, integration và coverage.
- `Black`/`Pylint`: format và static quality gate.
- `Tkinter`: GUI có sẵn trong Python, tránh runtime GUI dependency lớn.

## Decisions

- Network calls được mock/fake trong CI để test xác định và không phụ thuộc
  video bên thứ ba, geo-block hoặc rate limit.
- FFmpeg là dependency hệ thống tùy trường hợp; cần cho merge stream và MP3.
- Metadata preflight kiểm tra dung lượng nếu extractor cung cấp filesize.
- Batch cô lập lỗi theo URL và có cả chế độ tuần tự lẫn thread pool.
- URL detection dùng hostname suffix thay vì substring để chặn domain giả mạo.
- Cookie không được lưu trong repository và chỉ nhận qua đường dẫn cấu hình.

Coverage 86.41% tập trung vào core, config, factory, downloader adapter và
service. CLI/GUI mỏng được smoke test và loại khỏi phép đo coverage tự động.
