# Architecture and Technical Decisions

## Layers

1. **Models** chứa dữ liệu domain bất biến: platform, quality, metadata,
   progress và kết quả.
2. **Core** định nghĩa exception và `Downloader` protocol.
3. **Downloaders** là infrastructure adapter. Mỗi platform có class riêng nhưng
   tái sử dụng engine `YtDlpDownloader`.
4. **Services** thực hiện use case, kiểm tra dung lượng và cô lập lỗi batch.
5. **CLI/GUI** chỉ chuyển input thành lời gọi service và render output.

## Browser Downloader

`app/browser` là một bounded context riêng:

- `MediaDetector`: phân loại URL/MIME và suy luận quality.
- `MediaRequestInterceptor`: adapter QtWebEngine quan sát request, không sửa hay
  chặn traffic.
- `BrowserHttpClient`: HEAD hoặc Range probe giới hạn để lấy MIME/kích thước.
- `parse_hls_playlist`: phân tích master variants và từ chối dấu hiệu DRM.
- `BrowserDownloadManager`: task state machine cho Pause/Resume/Cancel, dùng
  resume `.part` của yt-dlp.

GUI dùng một `QWebEngineProfile` chung để browser tab chia sẻ cache/cookie.
Cookie, Referer và User-Agent được chuyển cho tác vụ tải đúng phiên hợp lệ.
Qt widget giao tiếp với download worker qua signal để không cập nhật UI từ
background thread.

Media detection kết hợp interceptor và JavaScript Performance API vì Qt không
cung cấp response MIME cho interceptor request. MIME được xác minh ngoài luồng
GUI bằng HTTP probe có timeout và giới hạn payload.

Thiết kế này giữ dependency direction từ ngoài vào trong và cho phép thay
`yt-dlp` bằng adapter khác thông qua protocol/factory.

## Why yt-dlp

Tự triển khai extractor cho bảy nền tảng sẽ dễ hỏng, đặc biệt với chữ ký URL,
manifest DASH/HLS, cookie và thay đổi frontend. `yt-dlp` cung cấp extractor được
bảo trì, format selection, fragment retry, progress hook, playlist và resume.

Adapter không trả dictionary của `yt-dlp` ra ngoài. Dữ liệu được chuyển thành
Pydantic models để giới hạn coupling với thư viện.

## Format Policy

- `best`: ưu tiên MP4 H.264 + AAC tương thích rộng, rồi fallback format tốt nhất.
- `1080p`, `720p`, `480p`: chọn chiều cao không vượt quá ngưỡng và fallback
  format ghép sẵn tương ứng.
- `audio`: chọn audio tốt nhất rồi chuyển sang MP3 192 kbps.

Các luồng tách rời và audio conversion cần FFmpeg. Không ép upscale khi nguồn
không có chất lượng yêu cầu.

## Reliability

- `continuedl=True` và `.part` cho resume.
- Retry request/fragment và timeout cấu hình được.
- Batch dùng `ThreadPoolExecutor`; lỗi một URL không hủy URL khác.
- Metadata được đọc trước download để kiểm tra dung lượng khi có filesize.
- Logging dùng `RotatingFileHandler` để tránh log tăng vô hạn.
- URL detector so khớp hostname/suffix, không tìm substring trong URL.

## Testing Strategy

Unit tests kiểm tra parser, detector, config, factory, option mapping, metadata
normalization, progress và error mapping. Integration tests ghép service với
fake downloader theo đúng contract để kiểm tra preflight/download/batch mà
không phụ thuộc mạng hoặc nội dung bên thứ ba.

Test mạng thật không chạy trong CI vì URL có thể bị xóa, rate-limit, geo-block
hoặc thay đổi metadata. Việc này làm CI không xác định. Smoke test thực tế được
thực hiện thủ công với nội dung công khai có quyền tải.
