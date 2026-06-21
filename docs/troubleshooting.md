# Troubleshooting Reference

## Diagnostic checklist

1. Xác nhận URL mở được trong trình duyệt trên cùng máy và cùng mạng.
2. Chạy `python --version`; yêu cầu Python 3.12 trở lên.
3. Chạy `ffmpeg -version` với preset audio hoặc format cần merge.
4. Cập nhật môi trường từ `requirements.txt`.
5. Chạy lại lệnh với `--verbose`.
6. Đọc lỗi mới nhất trong `logs/app.log`.
7. Nếu cần đăng nhập, làm mới cookie Netscape và không commit file này.

## Error mapping

| Nhóm lỗi | Hành vi |
|---|---|
| URL sai/nền tảng chưa hỗ trợ | Dừng trước khi gọi mạng |
| Riêng tư/đăng nhập | Hướng dẫn cấu hình cookie |
| Video xóa/không tồn tại | Trả `VideoUnavailableError` |
| Giới hạn vùng | Trả `GeoRestrictedError` |
| Timeout/kết nối | Trả `NetworkError`, giữ file `.part` |
| Thiếu dung lượng biết trước | Dừng trước download |
| Lỗi extractor khác | Log đầy đủ và hiện thông báo ngắn |
| HLS có DRM | Từ chối trước khi tạo tác vụ tải |
| Browser media URL hết hạn | Refresh trang và phát lại media |
| Pause | Giữ `.part`, Resume chạy lại với HTTP Range/fragment |

Trong batch, các lỗi này được lưu theo URL và các download còn lại tiếp tục.

## Browser diagnostics

Browser navigation, media detection và download lifecycle được ghi tại
`logs/browser.log`. Với trang dùng lazy loading, cần nhấn Play hoặc cuộn đến
video để Chromium thực sự request media. Signed URL có thể hết hạn và phải được
phát hiện lại trong cùng phiên.
