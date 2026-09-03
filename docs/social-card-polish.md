# Social card hover và GitHub logo polish

Ngày cập nhật: 2026-09-03  
Trạng thái: **Hoàn tất — production build pass**

## Kết quả

- Ba thẻ social vẫn theo thứ tự: **LinkedIn → GitHub → Facebook**.
- Hover của riêng nhóm social giảm từ `1.40×` xuống `1.14×`.
- LinkedIn được dịch trái `0.07` đơn vị và Facebook được dịch phải `0.07` đơn vị.
- Khoảng hở nghỉ mới là `0.095189` giữa LinkedIn/GitHub và `0.094171` giữa GitHub/Facebook.
- Ở scale mục tiêu `1.14×`, thẻ đang hover vẫn còn khoảng hở xấp xỉ `0.054–0.058`, nên không còn chạm thẻ kế bên.
- Các object khác trong phòng vẫn giữ nguyên hover cũ.

## GitHub logo

GitHub dùng shader riêng ở runtime, không sửa atlas Day/Night và không thay đổi GLB:

- Nền: GitHub black `#0D1117`.
- Logo ở trạng thái nghỉ: GitHub white `#F0F6FC`.
- Logo khi hover: pure white `#FFFFFF`.
- Giữ lại độ sáng tối nhẹ từ baked lighting để logo không bị phẳng.
- Giữ nguyên nền và cạnh gỗ của thẻ.
- Shader vẫn trộn đúng atlas Day/Night bằng `uMixRatio`.

Model runtime `room-main.glb` đã được kiểm tra trực tiếp sau giải nén Draco:

- Object: `GitHub_Fourth_Raycaster_Pointer_Hover`.
- `7,168` vertices, `10,638` polygons.
- `41` component topology thô sau giải nén Draco.
- Sau khi hàn ảo các đỉnh trùng nhau ở UV seam: `4` nhóm logic.
- Mask nhận diện đúng `3` nhóm logo (`7,042` vertices); nhóm nền/khung (`126` vertices) không đổi màu.

Phối màu đen/trắng tạo độ tương phản rõ ràng và gần với cách trình bày GitHub mark phổ biến, trong khi shader vẫn giữ một phần baked lighting để hình khối không bị phẳng.

- [GitHub Brand Toolkit — Logo](https://brand.github.com/foundations/logo)
- [GitHub Logo Policy](https://docs.github.com/en/site-policy/other-site-policies/github-logo-policy)

## File thay đổi

- [`src/main.js`](../src/main.js)
- [`src/shaders/github/vertex.glsl`](../src/shaders/github/vertex.glsl)
- [`src/shaders/github/fragment.glsl`](../src/shaders/github/fragment.glsl)
- [`scripts/blender/inspect_github_geometry.py`](../scripts/blender/inspect_github_geometry.py)
- [`artifacts/final-room-audit/github-geometry.json`](../artifacts/final-room-audit/github-geometry.json)

## Xác minh

- `npm run build`: Pass với Vite `6.4.3`.
- Production bundle: `dist/assets/index-Dr3XkZB9.js`.
- SHA-256 bundle: `B8A4AD5157F829783C3E0E4A1FC96AADC3A4BF9317B49A5CE51BA47061746A20`.
- Dev server trả HTTP `200` cho trang chính, `src/main.js`, hai shader GitHub và atlas Fourth Day.
- `git diff --check`: không có lỗi whitespace mới.
- Cảnh báo `eval` và bundle lớn đã tồn tại trong dự án, không chặn build và không phát sinh từ chỉnh sửa này.

Sau khi deploy lại, nên hard refresh trình duyệt để bỏ cache bundle cũ.
