# My Room - FINAL

Ngày chốt: 2026-09-02  
Trạng thái: **HOÀN TẤT — TOÀN DỰ ÁN CHỈ CÒN MỘT FILE BLENDER**

## File cuối

- [`My Room - FINAL.blend`](../blender%20files/My%20Room%20-%20FINAL.blend)
- SHA-256: `7EBCA579C94F380EC8D52E80FF168D9E012A9DDB36AC5D07EB4631572FAEEEF1`.
- Kích thước: `30,928,841` bytes.
- Render controller trên kệ: [`xbox-room-front.png`](../artifacts/xbox-controller-audit/xbox-room-front.png).

## Nội dung đã chốt

- `161` mesh căn phòng baked dùng Grounded Pastel Day trong trạng thái hiện tại.
- Có `LinkedIn_Fourth_Raycaster_Pointer_Hover` thay cho YouTube.
- Có `Facebook_Fifth_Raycaster_Pointer_Hover` đúng transform của `facebook-card.glb`.
- Có `Tree_3` đúng transform của `outside-tree.glb`.
- Có `Xbox_Controller_Raycaster_Hover` được dựng thẳng trên kệ bên trái.
- Không còn object Twitter.
- Đã loại `158` mesh authoring trùng khỏi **file cuối**.
- Bốn atlas Grounded Pastel `4096 × 4096` được pack vào `.blend`.
- Không còn đường dẫn texture ngoài bị thiếu.
- Facebook dùng màu nghỉ giống website: xanh `#455A86`, trắng `#DED8D4`.
- Tree material đã sửa `Principled Weight`, roughness/specular và có Day/fill lighting để không còn đen thùi trong Rendered mode.

## Kiểm tra tự động

| Check | Kết quả |
| --- | --- |
| Tổng mesh cuối | 165 |
| Baked room meshes | 161 |
| LinkedIn | Có, đang hiển thị |
| Facebook | Có, đang hiển thị |
| Tree_3 | Có, đang hiển thị |
| Xbox Controller | Có, dựng thẳng trên kệ |
| Twitter | 0 object |
| Atlas được pack | 4/4 |
| Kích thước atlas | 4096 × 4096 |
| Texture bị mất | 0 |
| Verification | Pass |

Artifact kiểm tra: [`final-room-verification.json`](../artifacts/final-room-audit/final-room-verification.json).

## Backup đã xóa

- Toàn bộ thư mục `backups/grounded-pastel-phase1-2026-09-01`.
- Blender đã tự tạo lại `My Room - FINAL.blend1` khi lưu controller; file production duy nhất vẫn là `My Room - FINAL.blend`.

Các thao tác xóa này không thể khôi phục từ workspace hiện tại.

## Tám file nguồn/test đã xóa vĩnh viễn

1. `artifacts/grounded-pastel-test/first-day-test-bake.blend`
2. `blender files/Before Baking - Grounded Pastel Test.blend`
3. `blender files/Before Baking.blend`
4. `blender files/For Export - Grounded Pastel Day.blend`
5. `blender files/For Export - Grounded Pastel Night.blend`
6. `blender files/For Export.blend`
7. `blender files/For Night Time Baking.blend`
8. `blender files/My Room.blend`

Các file trên gồm cả file authoring/baking gốc và không thể khôi phục từ workspace hiện tại.

Kiểm tra sau khi xóa:

- Tổng số file `.blend`/`.blend1` còn lại: `1`.
- File còn lại duy nhất: `blender files/My Room - FINAL.blend`.
- Blender 5.2.1 đã mở lại file cuối và verification vẫn `Pass`.

## File GLB được giữ lại

Các file sau không phải backup và vẫn được website tải trực tiếp, nên không xóa:

- `public/models/room-main.glb`
- `public/models/facebook-card.glb`
- `public/models/linkedin-card.glb`
- `public/models/outside-tree.glb`
- Các bản tương ứng trong `dist/models/`.
