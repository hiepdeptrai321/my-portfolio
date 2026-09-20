# PC theo bộ ảnh 3D tham chiếu — 2026-09-20

Bản hiện tại: **polish-v3**, tinh chỉnh từ studio-v2, lưu trong `blender files/My Room - FINAL.blend` và xuất sang `public/models/pc-upgrade.glb`.

Lần tinh chỉnh này chỉ sửa cách lắp quạt sau, vật liệu và ánh sáng PC. Đã bỏ góc xoay 55°, đặt mặt sau khung quạt sát mặt trong panel sau: khoảng hở đo được 0, trục quạt vuông góc panel. Geometry ngoài cụm quạt sau được đối chiếu và giữ nguyên, kể cả kích thước vỏ và bố trí linh kiện. Phòng và camera không thay đổi.

Ốc dùng xám kim loại nhẹ, lưới thoát khí có vật liệu tối hơn, khung trong và gá đỡ dùng xám lavender mát. Ambient occlusion phạm vi 0.045, cường độ 20% trên vỏ / 30% ở chi tiết, tạo bóng tiếp xúc nhẹ. Giảm đèn tím bên trong từ 60/18/20 xuống 25/6/8, LED từ 6 xuống 4.5 và halo web từ 0.24 xuống 0.16 để giữ chi tiết rõ.

PC được dựng lại theo bốn ảnh studio: vỏ trắng ngọc trai bo góc, kính trong, quạt LED lớn và quạt nhỏ phía sau, CPU có logo mèo/trái tim, hai thanh RAM phát sáng, hai ống tản nhiệt cong, ba quạt GPU lilac, lưới lỗ tròn trên nóc/sàn/mặt trước, cổng I/O và bốn chân đế. Collection `PC Reference Match` chứa 181 mesh có thể chỉnh riêng. Vị trí PC trên bàn được giữ, chiều cao vỏ tăng theo tỷ lệ mẫu.

| Phần | Màu sRGB vật liệu |
| --- | --- |
| Vỏ | `#F2ECE7` |
| Viền | `#CBC7D3` |
| Motherboard | `#C5B9D6` |
| Khung GPU | `#8B829C` |
| Quạt | `#C4B7D1` |
| Ống tản nhiệt | `#DDD1E8` |
| Ốc | `#9593A1` |
| Lưới | `#ABA5B5` |
| Gá đỡ | `#BAB5C6` |
| LED | `#E6BAFF` |

Vỏ nhận ánh sáng và bóng đổ. Kính dùng transmission 1, IOR 1.45, roughness 0.025. Đèn bổ sung được light-link riêng với PC. Compositor có thêm `PC Reference LED Bloom`, ngưỡng HDR 2 để làm mềm quầng LED. Mesh, UV, vật liệu và texture đồ vật khác, camera và color management gốc được giữ.

Ảnh kết quả:

- `artifacts/pc-reference-match/pc-studio-room.png`: bản polish-v3 trong phòng, render Cycles có kính, AO và ánh sáng đã giảm.
- `artifacts/pc-reference-match/pc-studio-hero.png`: lưu trữ ảnh studio-v2 trước lần tinh chỉnh này.
- `artifacts/pc-reference-match/pc-web-export-preview.png`: mở chính GLB đã xuất, render atlas bằng emission để kiểm tra hình học, UV và màu. Ảnh này không mô phỏng kính WebGL hoặc halo JavaScript.

Đây là bản dựng đối chiếu bằng mắt từ ảnh. Không có model, camera và ánh sáng gốc để xác nhận trùng từng pixel.

## Website

GLB có 9 mesh: vỏ/nội thất đã gộp, kính và bảy LED. Ánh sáng diffuse, bóng đổ, AO và màu được bake vào atlas **4096 × 4096** nhúng trong GLB. File dùng Draco, dung lượng 9.37 MB; UV và vị trí được lưu với độ chính xác 16 bit để hạn chế sai lệch ở cạnh chi tiết.

`src/main.js` tải `/models/pc-upgrade.glb?v=20260920-pc-polish-v3`. Shader lấy atlas thay bảng màu cũ và giữ chuyển đổi ngày/đêm. Mỗi LED có halo tím nhỏ theo mặt phát sáng, có depth test để đồ vật phía trước che đúng.

`npm run dev` dùng model trong `public/models`, không tự xuất file `.blend`. Sau khi chỉnh Blender cần xuất lại GLB. Revision URL giúp tránh cache model cũ.

## Tái tạo và kiểm tra

Chạy ở thư mục gốc bằng Blender 5.2:

```powershell
blender --background 'blender files/My Room - FINAL.blend' --python-exit-code 1 --python scripts/blender/rebuild_pc_studio_reference.py -- --final
blender --background 'blender files/My Room - FINAL.blend' --python-exit-code 1 --python scripts/blender/rebuild_pc_studio_reference.py -- --commit --no-render
blender --background --python-exit-code 1 --python scripts/blender/verify_pc_reference_preservation.py -- --polish
blender --background 'blender files/My Room - FINAL.blend' --python-exit-code 1 --python scripts/blender/export_pc_reference_web.py
npm run build
# Khi dev server đang chạy ở cổng 5173:
node scripts/verify-pc-web.mjs
```

Thêm `--front` hoặc `--room` vào script dựng để đổi góc kiểm tra. Script xuất chỉ chỉnh bản trong bộ nhớ, không ghi đè Blender hay atlas phòng. `match_pc_reference.py` là phiên bản cũ; không dùng để tái tạo studio-v2.

Kết quả:

- Preservation **PASS**: geometry ngoài cụm quạt sau giữ nguyên; 166 object ngoài PC, 7 ảnh, 14 vật liệu ngoài PC và camera không thay đổi so với backup trước polish-v3.
- Mở lại Blender **PASS**: 345 mesh, đủ 161 baked room mesh, không thiếu texture ngoài.
- Build Vite **PASS**, còn cảnh báo có sẵn về `eval` và kích thước chunk.
- GLB, bản build và dữ liệu từ dev server có cùng SHA-256; revision mới được phục vụ đúng.
- Đã xem render Cycles và render từ GLB thực tế. Chưa kiểm tra hình ảnh trực tiếp bằng trình duyệt: Browser không kết nối được; Computer Use dừng vì không xác định được URL hiện tại.

Báo cáo: `artifacts/pc-reference-match/` và `artifacts/final-room-audit/`. Backup lần tinh chỉnh: `artifacts/pc-reference-match/backup/My Room - before-polish.blend`, giữ trên máy và loại khỏi Git.
