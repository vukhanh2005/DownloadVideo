# Multi-platform Video Downloader

Ứng dụng Python 3.12+ tải video và audio bằng CLI hoặc giao diện PySide6. Backend
`yt-dlp` hỗ trợ:

- YouTube và playlist YouTube
- Facebook
- Instagram
- TikTok
- X (Twitter)
- Vimeo
- Dailymotion

Chỉ tải nội dung bạn có quyền truy cập và quyền lưu trữ. Người dùng chịu trách
nhiệm tuân thủ điều khoản dịch vụ và luật bản quyền áp dụng.

## Tính năng

- Tự nhận diện nền tảng bằng hostname an toàn.
- Đọc tiêu đề, tác giả, thời lượng, thumbnail, format và dung lượng ước tính.
- Preset `best`, `1080p`, `720p`, `480p`, `audio`.
- Playlist, batch tuần tự hoặc song song.
- Progress bar có phần trăm, tốc độ, dung lượng và ETA.
- Resume qua file `.part`, retry request và fragment.
- YAML config được kiểm tra bằng Pydantic.
- Log xoay vòng tại `logs/app.log`.
- CLI Typer/Rich và GUI PySide6/QtWebEngine.
- Browser Downloader nhiều tab, tự phát hiện MP4/WebM/HLS/audio không DRM.
- Download Manager hỗ trợ Pause, Resume và Cancel.
- Unit/integration test không phụ thuộc mạng.

## Cài đặt

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Linux/macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### FFmpeg

Ứng dụng tự tìm FFmpeg trong `PATH` hoặc dùng binary từ `imageio-ffmpeg`.
Có thể ép dùng một bản FFmpeg khác bằng cấu hình:

```yaml
ffmpeg_path: C:/tools/ffmpeg/bin/ffmpeg.exe
```

FFmpeg được dùng khi nguồn cung cấp video và audio thành các luồng riêng và khi
chuyển audio sang MP3. Bản Windows EXE đã đóng gói sẵn binary này.

## Sử dụng CLI

```bash
# Xem metadata
python main.py info "https://www.youtube.com/watch?v=VIDEO_ID"

# Tải chất lượng tốt nhất
python main.py download "https://www.youtube.com/watch?v=VIDEO_ID"

# Tải tối đa 720p
python main.py download URL --quality 720p

# Tách audio MP3 192 kbps
python main.py download URL --quality audio

# Liệt kê playlist
python main.py playlist PLAYLIST_URL --metadata-only

# Tải toàn bộ playlist
python main.py playlist PLAYLIST_URL --quality 1080p

# Tải urls.txt song song
python main.py batch urls.txt

# Tải batch tuần tự
python main.py batch urls.txt --sequential

# Mở GUI
python main.py gui
```

## Browser Downloader

Tab **Browser Downloader** là trình duyệt Chromium tích hợp dành cho media mà
người dùng có quyền truy cập. Thanh điều hướng hỗ trợ Back, Forward, Refresh,
Home, Go và nhiều browser tab.

Khi trang tải media, ứng dụng tự động:

1. Theo dõi network request của QtWebEngine.
2. Quét thẻ `video`, `audio`, `source` và Performance Resource API.
3. Nhận diện MP4, WebM, M3U8, MP3, M4A, AAC, OGG và Opus.
4. Đọc MIME, kích thước và HLS variants bằng request giới hạn.
5. Hiển thị nút Download cho từng dòng.

Download Manager phía dưới hiển thị trạng thái, phần trăm, tốc độ, ETA và file
đầu ra. `Pause` dừng tác vụ nhưng giữ file `.part`; `Resume` tiếp tục từ dữ liệu
đã tải; `Cancel` dừng và xóa file tạm.

Ví dụ sử dụng:

1. Mở tab Browser Downloader.
2. Nhập URL blog hoặc trang học tập có video công khai.
3. Phát video nếu trang chỉ tải media sau tương tác.
4. Chọn quality HLS được phát hiện và nhấn Download.

Ứng dụng không giải mã DRM, không vượt paywall, không bỏ qua đăng nhập và không
can thiệp cơ chế bảo vệ nội dung. HLS có dấu hiệu Widevine, FairPlay, PlayReady
hoặc SAMPLE-AES sẽ bị từ chối.

## Build Windows EXE

```powershell
python -m pip install -r requirements-dev.txt
pyinstaller --clean --noconfirm VideoDownloader.spec
.\dist\VideoDownloader.exe
```

File `dist/VideoDownloader.exe` mở trực tiếp giao diện Qt. Bản đóng gói chứa
Python, thư viện ứng dụng và FFmpeg để ghép luồng hoặc xuất MP3.

Sau khi cài project bằng `pip install .`, lệnh `video-downloader` tương đương
`python main.py`.

## Cấu hình

`config.yaml`:

```yaml
download_path: downloads
max_threads: 3
default_quality: best
retries: 10
fragment_retries: 10
socket_timeout: 30
concurrent_fragments: 4
output_template: "%(title).60B [%(id)s].%(ext)s"
cookies_file:
ffmpeg_path:
log_path: logs/app.log
browser_log_path: logs/browser.log
```

`max_threads` điều khiển số URL batch chạy đồng thời. `concurrent_fragments`
điều khiển số fragment của một video được tải đồng thời. Giới hạn hai giá trị
này để tránh rate limit và chiếm hết băng thông.

Với nội dung riêng tư hoặc cần đăng nhập, xuất cookie ở định dạng Netscape,
lưu ngoài Git (ví dụ `cookies.txt`) và đặt:

```yaml
cookies_file: cookies.txt
```

Không chia sẻ file cookie vì nó có thể chứa phiên đăng nhập.

## Kiến trúc

```text
app/
├── browser/      # detector, HLS, HTTP probe, download manager
├── config/       # YAML và validation
├── core/         # exception, protocol
├── downloaders/  # adapter yt-dlp và platform factory
├── models/       # model domain Pydantic
├── services/     # use case metadata/download/batch
├── utils/        # URL, logging, formatting
├── cli.py
└── gui/          # PySide6 classic tab và Browser Downloader
```

Luồng phụ thuộc là UI -> service -> protocol/factory -> downloader adapter.
Model domain không phụ thuộc UI. Để thêm nền tảng, tạo adapter với `platform`,
đăng ký trong `DownloaderFactory`, rồi bổ sung domain vào detector.

Browser Downloader dùng QWebEngine interceptor như adapter Qt. Detector, HTTP
probe, HLS parser và download manager không phụ thuộc widget nên có thể test độc
lập.

Chi tiết quyết định kỹ thuật nằm tại
[`docs/architecture.md`](docs/architecture.md).

## Kiểm thử và chất lượng

```bash
python -m pip install -r requirements-dev.txt
black --check .
ruff check .
pylint app main.py
pytest
```

Coverage loại trừ CLI/GUI mỏng và yêu cầu tối thiểu 80% cho logic ứng dụng.
GitHub Actions chạy Black, Pylint và toàn bộ test trên Python 3.12 và 3.13.

## Xử lý sự cố

### Video riêng tư hoặc yêu cầu đăng nhập

Thiết lập `cookies_file`. Cookie phải ở định dạng Netscape và còn hiệu lực.

### YouTube yêu cầu xác nhận không phải bot

Cập nhật `yt-dlp`, giảm số luồng, chờ hết rate limit, hoặc dùng cookie hợp lệ.
Không tắt kiểm tra TLS.

### Video bị giới hạn vùng

Ứng dụng trả lỗi rõ ràng thay vì crash. Chỉ truy cập nội dung được phép tại khu
vực của bạn.

### Lỗi `ffmpeg is not installed`

Cài lại dependencies hoặc bản EXE mới. Nếu dùng FFmpeg riêng, đặt `ffmpeg_path`
đến executable hợp lệ.

### Mạng bị ngắt

Chạy lại cùng lệnh. `yt-dlp` tiếp tục từ file `.part` nếu server nguồn hỗ trợ
HTTP range hoặc giao thức fragment.

### Hết dung lượng

Ứng dụng kiểm tra dung lượng nếu extractor cung cấp filesize. Với stream không
có kích thước, kiểm tra ổ đĩa thủ công; lỗi ghi đĩa vẫn được log và chuyển thành
thông báo thân thiện.

### Extractor đột ngột lỗi

Các nền tảng thường thay đổi giao diện. Cài bản `yt-dlp` mới tương thích, chạy
lại với `--verbose`, rồi xem `logs/app.log`.

### Browser không phát hiện video

Nhấn Play để trang phát sinh network request, sau đó chờ vài giây hoặc Refresh.
Media qua `blob:` chỉ được tải khi URL HTTP nguồn xuất hiện trong request hoặc
Performance API. Nội dung DRM không được thêm vào danh sách tải.

### Browser hiển thị trang trắng

Cập nhật driver đồ họa. Trên máy ảo hoặc Remote Desktop, QtWebEngine có thể tự
fallback sang software rendering. Xem `logs/browser.log` để kiểm tra URL và lỗi.

### HLS tải lỗi

URL manifest có thể hết hạn hoặc yêu cầu phiên duyệt. Hãy tải ngay trong cùng
phiên browser. Cookie và Referer hiện tại được chuyển cho download manager.

## Giới hạn thực tế

- Chất lượng khả dụng phụ thuộc video, tài khoản, vùng và extractor.
- Dung lượng chỉ là ước tính khi nguồn không cung cấp `filesize`.
- Một số URL cần cookie hoặc xác minh của nền tảng.
- Playlist ngoài YouTube hoạt động nếu extractor tương ứng cung cấp entries.
