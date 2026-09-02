# Grounded Pastel Blender files

> Báo cáo này đã được thay thế bởi [`my-room-final.md`](./my-room-final.md). File được chốt hiện tại là `My Room - FINAL.blend`, có cả Facebook và `Tree_3`.

Ngày tạo: 2026-09-02  
Trạng thái: **HOÀN TẤT — FILE GỐC KHÔNG BỊ GHI ĐÈ**

## File nên mở

### Grounded Pastel Day

- [`For Export - Grounded Pastel Day.blend`](../blender%20files/For%20Export%20-%20Grounded%20Pastel%20Day.blend)
- Kích thước: `37,553,134` bytes.
- SHA-256: `ED09A1FA5B8BA2160BFA61277E433689174F12463E012CDCA63E3D2D326AC048`.
- Chứa bốn atlas Grounded Pastel Day đã được duyệt.

### Grounded Pastel Night

- [`For Export - Grounded Pastel Night.blend`](../blender%20files/For%20Export%20-%20Grounded%20Pastel%20Night.blend)
- Kích thước: `31,933,106` bytes.
- SHA-256: `E014A3373E771694552D4329D822D5004928BF9A6C6E658D8F022E0193C9EFEF`.
- Chứa bốn atlas Grounded Pastel Night test.

## Màu được gắn vào Blender như thế nào

Hai file là bản sao an toàn của `For Export.blend`.

Bốn baked materials được cập nhật:

| Texture set | Baked material |
| --- | --- |
| First | `FinalFirst_Baked` |
| Second | `RealFinalSecond_Baked` |
| Third | `FinalThird_Baked` |
| Fourth | `FinalFourth_Baked` |

Trong file Day, mỗi material dùng đúng Grounded Pastel Day atlas. Trong file Night, mỗi material dùng đúng Grounded Pastel Night atlas.

Tất cả ảnh đều:

- Có kích thước `4096 × 4096`.
- Dùng color space `sRGB`.
- Được nối trực tiếp `Image Texture → Emission` giống cấu trúc baked material gốc.
- Được **Pack Resources** vào trong `.blend`, nên không phụ thuộc đường dẫn texture bên ngoài khi di chuyển file.

## Cách xem màu trong Blender

1. Mở file Day hoặc Night tương ứng.
2. Chuyển viewport sang **Material Preview** hoặc **Rendered**.
3. Nếu đang ở Solid mode, màu atlas sẽ không hiển thị chính xác.

Hai file được lưu ở **Object Mode** với collection `SimpleBake_Bakes` đang bật.
Các mesh nguồn dùng để bake vẫn được giữ nguyên trong file nhưng được ẩn khỏi viewport và render.

## Sửa lỗi viewport màu hồng ngày 2026-09-02

Nguyên nhân đã xác định:

- Collection `SimpleBake_Bakes` chứa `166` mesh đúng màu đã bị `Exclude` trong View Layer.
- `165` mesh nguồn lại đang hiển thị; một số texture ngoài của chúng không còn được Blender tìm thấy nên Blender báo lỗi bằng màu hồng/magenta.
- Đây không phải màu của Grounded Pastel atlas và không phải lỗi thao tác của người mở file.

Trạng thái sau khi sửa ở cả Day và Night:

| Nhóm mesh | Tổng số | Viewport | Render |
| --- | ---: | --- | --- |
| Baked Grounded Pastel | 166 | Bật 166/166 | Bật 166/166 |
| Source/baking meshes | 165 | Ẩn 165/165 | Ẩn 165/165 |

Nếu file màu hồng vẫn đang mở trong Blender trong lúc bản sửa được tạo, hãy **đóng cửa sổ đó và chọn Don't Save**, sau đó mở lại file từ ổ đĩa. Không lưu cửa sổ cũ vì thao tác đó sẽ ghi đè bản đã sửa.

Lệnh mở Day:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" ".\blender files\For Export - Grounded Pastel Day.blend"
```

Lệnh mở Night:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" ".\blender files\For Export - Grounded Pastel Night.blend"
```

## Kết quả xác minh

Cả hai file đã được Blender 5.2.1 mở lại sau khi lưu.

| Check | Day | Night |
| --- | --- | --- |
| 4 baked materials tồn tại | Pass | Pass |
| 4 Grounded images được pack | Pass | Pass |
| Mỗi image là `4096 × 4096` | Pass | Pass |
| Image Texture nối tới Emission | Pass | Pass |
| `SimpleBake_Bakes` không còn bị Exclude | Pass | Pass |
| 166 baked meshes hiển thị | Pass | Pass |
| 165 source meshes được ẩn | Pass | Pass |
| Object count | 333 | 333 |
| Mesh object count | 331 | 331 |
| Vertex count | 443,882 | 443,882 |
| Polygon count | 412,028 | 412,028 |
| UV loop count | 1,819,620 | 1,819,620 |

Geometry/UV structure SHA-256:

```text
Original For Export: ADFD76A59F4CBE2868AFD9232DFA82C1B09666DCB1E1962365ADFE8334297EF1
Grounded Day:       ADFD76A59F4CBE2868AFD9232DFA82C1B09666DCB1E1962365ADFE8334297EF1
Grounded Night:     ADFD76A59F4CBE2868AFD9232DFA82C1B09666DCB1E1962365ADFE8334297EF1
```

Kết luận: object names, transforms, mesh geometry, material-slot assignments, polygon indices và UV data đều khớp file gốc.

Render kiểm chứng trực tiếp bằng Blender 5.2.1:

- [`Grounded Pastel Day validation`](../artifacts/grounded-pastel-no-rebake/for-export---grounded-pastel-day-validation.png)
- [`Grounded Pastel Night validation`](../artifacts/grounded-pastel-no-rebake/for-export---grounded-pastel-night-validation.png)

Cả hai render đều hiển thị atlas đúng màu và không còn vật thể magenta.

## File gốc được bảo vệ

`For Export.blend` vẫn giữ nguyên:

- SHA-256: `BB381A2FA9B3729C44FD7F5FC489E064E2F3EFC50E39ED014D8D85BEB5E7188B`.
- Khớp backup Phase 1.
- Không bị ghi đè.

`Before Baking.blend` và `For Night Time Baking.blend` cũng không bị sửa.

## Giới hạn cần hiểu rõ

Hai file mới là **baked-material preview/export files**. Chúng hiển thị chính xác màu Grounded Pastel đang dùng trên website và phù hợp để xem scene hoặc xuất model với baked atlas.

Chúng không chuyển đổi ngược atlas thành hàng trăm material nguồn riêng lẻ trong `Before Baking.blend`. Nếu cần chỉnh từng source material như `Room`, `Chair Cushion`, `Computer` hoặc `Drawer` bằng color picker rồi bake lại, đó sẽ là một bước authoring/rebake riêng.

## Scripts và verification artifacts

- [`create_grounded_pastel_static_export_blend.py`](../scripts/blender/create_grounded_pastel_static_export_blend.py)
- [`verify_grounded_pastel_static_blend.py`](../scripts/blender/verify_grounded_pastel_static_blend.py)
- [`render_grounded_pastel_validation.py`](../scripts/blender/render_grounded_pastel_validation.py)
- [`grounded-pastel-day-blend-create.json`](../artifacts/grounded-pastel-no-rebake/grounded-pastel-day-blend-create.json)
- [`grounded-pastel-night-blend-create.json`](../artifacts/grounded-pastel-no-rebake/grounded-pastel-night-blend-create.json)
- [`for-export-grounded-pastel-day-verification.json`](../artifacts/grounded-pastel-no-rebake/for-export-grounded-pastel-day-verification.json)
- [`for-export-grounded-pastel-night-verification.json`](../artifacts/grounded-pastel-no-rebake/for-export-grounded-pastel-night-verification.json)

Một file preview động tạm thời đã được loại bỏ vì Blender 5.2 không cập nhật material-node driver một cách đáng tin cậy khi mở lại. Nó được thay bằng hai file Day/Night độc lập ở trên; cách này ổn định và không cần chạy script khi mở file.
