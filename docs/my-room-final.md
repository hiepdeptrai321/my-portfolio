# My Room - FINAL

Ngày chốt: 2026-09-02  
Trạng thái: **HOÀN TẤT — TOÀN DỰ ÁN CHỈ CÒN MỘT FILE BLENDER**

## File cuối

- [`My Room - FINAL.blend`](../blender%20files/My%20Room%20-%20FINAL.blend)
- SHA-256: `10072F4E41D4851ACA845D0CF051B4563B7048FA58F61B4FCAB04165134A5C4B`.
- Kích thước: `28,349,179` bytes.
- Render kiểm chứng: [`my-room---final-validation.png`](../artifacts/grounded-pastel-no-rebake/my-room---final-validation.png).

## Nội dung đã chốt

- `165` mesh căn phòng baked dùng Grounded Pastel Day.
- Có `Facebook_Fifth_Raycaster_Pointer_Hover` đúng transform của `facebook-card.glb`.
- Có `Tree_3` đúng transform của `outside-tree.glb`.
- Không còn object Twitter.
- Đã loại `158` mesh authoring trùng khỏi **file cuối**.
- Bốn atlas Grounded Pastel `4096 × 4096` được pack vào `.blend`.
- Không còn đường dẫn texture ngoài bị thiếu.
- Facebook dùng màu nghỉ giống website: xanh `#455A86`, trắng `#DED8D4`.
- Tree material đã sửa `Principled Weight`, roughness/specular và có Day/fill lighting để không còn đen thùi trong Rendered mode.

## Kiểm tra tự động

| Check | Kết quả |
| --- | --- |
| Tổng mesh cuối | 167 |
| Baked room meshes | 165 |
| Facebook | Có, đang hiển thị |
| Tree_3 | Có, đang hiển thị |
| Twitter | 0 object |
| Atlas được pack | 4/4 |
| Kích thước atlas | 4096 × 4096 |
| Texture bị mất | 0 |
| Verification | Pass |

Artifact kiểm tra: [`final-room-verification.json`](../artifacts/final-room-audit/final-room-verification.json).

## Backup đã xóa

- Toàn bộ thư mục `backups/grounded-pastel-phase1-2026-09-01`.
- Toàn bộ file `.blend1`; số file `.blend1` còn lại là `0`.

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
- `public/models/outside-tree.glb`
- Các bản tương ứng trong `dist/models/`.
