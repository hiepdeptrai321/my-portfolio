# Sửa controller bị đen và chồng object cũ

Ngày cập nhật: 2026-09-03  
Trạng thái: **Đã sửa code và production build thành công**

## Nguyên nhân

- Controller dùng material PBR và một lớp đèn riêng. Cách này không tương thích ổn định với cấu hình ánh sáng hiện tại nên toàn bộ controller bị render gần như màu đen.
- `room-main.glb` vẫn chứa object khung ảnh cũ `Frame_3_Second_Raycaster_Hover` đúng tại vị trí controller mới, nên hai object nằm chồng lên nhau.

## Thay đổi đã thực hiện

- Thay material PBR của controller bằng shader riêng, không còn phụ thuộc vào đèn bổ sung.
- Đổi phần vỏ đen/xám sang bảng màu Grounded Pastel:
  - Deep Sage: `#405D52`
  - Mist Gray: `#DCE2DE`
  - Khi hover: Sage `#718E7A` và Warm Cream `#F1E9DE`
- Giữ lại chi tiết màu của các nút Xbox từ texture gốc.
- Thêm shading mềm dựa trên normal để controller vẫn có khối, không bị phẳng.
- Giữ nguyên hover phóng to `1.12×` và nâng lên `0.08` đơn vị.
- Controller bắt đầu với scale `0` và xuất hiện sau Facebook trong chuỗi intro, dùng cùng nhịp `back.out(1.8)` với các thẻ profile.
- Hitbox của controller chỉ được kích hoạt sau khi animation xuất hiện hoàn tất, tránh hover khi object còn đang ẩn.
- Ẩn `Frame_3_Second_Raycaster_Hover` và loại object này khỏi raycaster.
- Vẫn giữ node khung ảnh cũ trong scene graph để timeline intro hiện tại không bị lỗi.

## File thay đổi

- [`src/main.js`](../src/main.js)
- [`src/shaders/xbox/vertex.glsl`](../src/shaders/xbox/vertex.glsl)
- [`src/shaders/xbox/fragment.glsl`](../src/shaders/xbox/fragment.glsl)

Không cần sửa hoặc xuất lại file `.blend`/`.glb` cho bản vá này.

## Xác minh

- `npm run build`: **Pass**.
- Production JS: `dist/assets/index-D70fKXIz.js`.
- SHA-256 production JS: `60D54212F3A93D5C89F0CDD1FE6CE6E43FE64D55DEDE624EE606F5F2887652E2`.
- Trang chính, `src/main.js` và `xbox-controller.glb`: HTTP `200` trên dev server.
- `public/models/xbox-controller.glb` và bản trong `dist` có cùng SHA-256:
  `9D2994E3829541BC3BBF3D3476E43703A6BD18257A24F2BC287876321FAFE5AD`.
- Không có trình duyệt điều khiển được kết nối trong phiên này, nên chưa thể chụp ảnh xác minh WebGL tự động. Cần kiểm tra hình ảnh cuối bằng refresh cứng trên trình duyệt sau khi chạy hoặc deploy bản build mới.
