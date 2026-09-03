# Volume value UI

Ngày cập nhật: 2026-09-03  
Trạng thái: **Hoàn tất**

## Thay đổi

- Bỏ ký hiệu `%` khỏi số âm lượng hiển thị.
- Tăng cỡ chữ từ `0.75rem` lên `1rem`.
- Tăng độ đậm từ `750` lên `850`.
- Căn giữa số và dùng `tabular-nums` để chiều rộng ổn định khi giá trị thay đổi.
- Giữ nguyên ký hiệu `%` trong `aria-valuetext` để trình đọc màn hình vẫn diễn giải đúng đơn vị âm lượng.
- Không thay đổi logic slider, mute hoặc âm lượng thực tế.

## File thay đổi

- [`index.html`](../index.html)
- [`src/main.js`](../src/main.js)
- [`src/style.scss`](../src/style.scss)

## Xác minh

- Giá trị HTML mặc định hiển thị là `50`.
- JavaScript cập nhật các giá trị dạng `0` đến `100`, không nối `%` vào nội dung nhìn thấy.
- `npm run build`: Pass với Vite `6.4.3`.
- Production assets: `index-DNAwgzVO.js` và `index-y74iNUV2.css`.
