# PC area upgrade

Ngày cập nhật: 2026-09-03  
Trạng thái: **Hoàn tất Blender, model web, Day/Night integration và production build**

## Kết quả

Chỉ khu vực PC được thay đổi. Layout căn phòng, camera, kích thước case, room atlas, UV và các đồ trang trí khác được giữ nguyên. Bản trắng–sage đầu tiên đã được thay bằng hướng blush–mauve–lavender theo ảnh tham chiếu của người dùng.

### Stage 1 — Case materials

| Thành phần | Màu mới | Hex |
| --- | --- | --- |
| Vỏ case chính | Blush White | `#EADDE3` |
| Viền và chi tiết case | Lavender Mist | `#D8C7DD` |
| Kính hông | Lavender tinted glass | `#D9CBE5` |
| Nội thất trung tính | Mauve Gray | `#8F8193` |

- `Plane.020_Baked` vẫn giữ nguyên `2,904` vertices và `2,439` polygons.
- Không thay đổi kích thước, vị trí hoặc hình dáng case.
- Kính mới trong suốt nhẹ, có tint xanh–xám lạnh và không ghi depth trên web.

### Stage 2 — Internal details

Đã bổ sung hoặc làm rõ các chi tiết toy-like, không hyper-realistic:

- motherboard Mauve;
- CPU block Mist Gray;
- hai RAM block Dusty Blue và Lavender;
- GPU block Muted Plum;
- ba vòng cooling fan;
- hai cable hint bo tròn.

Các màu nội thất:

| Thành phần | Màu | Hex |
| --- | --- | --- |
| Motherboard | Mauve | `#A582A4` |
| GPU | Muted Plum | `#74617F` |
| Internal accents | Soft Lavender | `#BBA8CC` |
| Fan accents | Pastel Lilac | `#CBB3DB` |

### Stage 3 — Pastel purple LED

- Quạt phía trên bên trái có một vòng RGB-style lavender và halo mềm, khớp bố cục ảnh tham chiếu.
- Ba quạt GPU phía dưới dùng Lavender Mist; vòng giữa có thêm glow nhẹ.
- Thêm LED strip mảnh dọc đáy case cùng halo nhẹ.
- Màu LED: `#D8B5EE`.
- Đèn `Point` cũ bên trong PC được đổi sang lavender mềm, energy `55`, shadow size `0.38`.
- Web có thêm radial ambient glow bán trong suốt bên trong case để tạo lớp ánh tím xuyên qua kính mà không cần bloom nặng.
- Không dùng rainbow RGB hoặc neon bão hòa cao.

### Stage 4 — Visual harmony

- Blush White nối màu với ghế peach, desk mat và tông hồng ấm trong ảnh tham chiếu.
- Mauve/Muted Plum làm nội thất PC rõ hơn nhưng vẫn mềm và toy-like.
- Lavender liên kết với poster, loa và phụ kiện tím nhưng không biến PC thành focal point chính.
- Web shader có màu Day/Night riêng; khi đổi theme, PC tối dần trong `1.5s` cùng căn phòng, trong khi LED lavender vẫn phát sáng nhẹ.

## Web implementation

- Model PC bổ sung: [`pc-upgrade.glb`](../public/models/pc-upgrade.glb).
- Model gồm `17` mesh, `9` material, không dùng texture ảnh và đã bật Draco compression level `6`.
- Kích thước GLB: `69,684` bytes.
- SHA-256 GLB: `2999BAD3A90ECA006B72289B7BD569746ED33FDEA197955085852F43B5802BBC`.
- Case overlay dùng polygon offset để phủ sạch màu xanh baked cũ mà không sửa tám room atlas.
- Các fan gốc và kính gốc trong `room-main.glb` được đổi vật liệu riêng ở runtime; animation fan hiện có vẫn được giữ.

## Xác minh

- Blender verification: **Pass**.
- Final Blender: `184` objects, gồm `181` mesh.
- Baked room meshes: `161`, không thay đổi.
- PC upgrade meshes mới: `16`.
- Missing external images: `0`.
- Final Blender SHA-256: `0638C08AD9E306F509FDB98B8FC1AF77EE24CF5BA05C822F95F8129A9B2B55FF`.
- `npm run build`: **Pass** với Vite `6.4.3`.
- Production JS: `dist/assets/index-DIhkyJj9.js`.
- Production JS SHA-256: `7B2F15016F7C6C36F24B534A9403EE9D99D63CAF99F5B9F0B1329DF1F435DAFD`.
- Trang chính, `src/main.js`, hai PC shader và `pc-upgrade.glb` đều trả HTTP `200` trên dev server.
- `public/models/pc-upgrade.glb` và `dist/models/pc-upgrade.glb` có cùng SHA-256.

## Preview

- [Trước khi nâng cấp](../artifacts/pc-upgrade/pc-room-context-before.png)
- [Sau khi nâng cấp](../artifacts/pc-upgrade/pc-room-context-after.png)
- [Case geometry gốc](../artifacts/pc-upgrade/pc-case-isolated.png)

## File thay đổi chính

- [`My Room - FINAL.blend`](../blender%20files/My%20Room%20-%20FINAL.blend)
- [`src/main.js`](../src/main.js)
- [`pc-upgrade.glb`](../public/models/pc-upgrade.glb)
- [`PC vertex shader`](../src/shaders/pc/vertex.glsl)
- [`PC fragment shader`](../src/shaders/pc/fragment.glsl)
- [`upgrade_pc_area.py`](../scripts/blender/upgrade_pc_area.py)
- [`verify_final_room_blend.py`](../scripts/blender/verify_final_room_blend.py)

## Lưu ý kiểm tra cuối

Ảnh Blender đã được render và kiểm tra trực tiếp. Phiên làm việc hiện không có trình duyệt điều khiển được kết nối, vì vậy hình WebGL cuối cần được kiểm tra bằng refresh cứng (`Ctrl + F5`) sau khi chạy local hoặc deploy build mới.
