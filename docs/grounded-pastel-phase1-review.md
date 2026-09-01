# Báo cáo review Grounded Pastel — Staged workflow

Ngày thực hiện: 2026-09-01  
Trạng thái: **DỪNG SAU MỘT ATLAS TEST — KHÔNG BAKE BẢY ATLAS CÒN LẠI**

## Kết luận ngắn

- Backup hoàn tất và đã xác minh SHA-256.
- Shader theme đã trở về kiến trúc gốc: Day texture + Night texture + `uMixRatio`; không còn uniform recolor/tint toàn cục.
- Palette Grounded Pastel chỉ được áp dụng vào bản copy của `Before Baking.blend`.
- Geometry, UV và object name của bản nguồn palette không đổi.
- UI Light đã dùng đúng Deep Sage, Sage, Soft Sage, Warm Cream, Mist Gray và Text theo yêu cầu.
- `npm run build` thành công.
- Atlas Day test số 1 đã bake riêng ở 4096×4096, nhưng **không đạt** do vùng transparent/ray-miss lớn, nhiều vùng tối/đen và khác workflow SimpleBake rõ rệt.
- Cả 8 atlas production và 3 file Blender nguồn vẫn trùng backup sau toàn bộ quá trình: **11/11 file không đổi**.

## 1. Backup và trạng thái an toàn

Backup nằm tại:

`backups/grounded-pastel-phase1-2026-09-01/`

Đã backup:

- 4 atlas Day production.
- 4 atlas Night production.
- `Before Baking.blend`.
- `For Export.blend`.
- `For Night Time Baking.blend`.
- Bản shader trước khi khôi phục.

Manifest và SHA-256 đầy đủ:

`backups/grounded-pastel-phase1-2026-09-01/README.md`

Tên texture của fork vẫn được giữ nguyên dạng gạch ngang, ví dụ:

- `first-texture-set-day.webp`
- `first-texture-set-night.webp`
- `second-texture-set-day.webp`
- `third-texture-set-day.webp`
- `fourth-texture-set-day.webp`

`textureMap` trong `src/main.js` vẫn tham chiếu các filename này. Không đổi tên sang dạng gạch dưới của upstream.

## 2. Shader đã khôi phục

File:

`src/shaders/theme/fragment.glsl`

Kiến trúc hiện tại:

1. Chọn một trong bốn cặp Day/Night bằng `uTextureSet`.
2. Đọc `dayColor` và `nightColor` từ atlas.
3. Trộn bằng `mix(dayColor, nightColor, uMixRatio)`.
4. Không dùng uniform recolor, tint hoặc thay palette toàn cảnh.

Các uniform recolor tạm trước đó cũng đã được loại khỏi `src/main.js`.

SHA-256 shader đã khôi phục:

`19356A3829F0FDAC6DDBEE594A149241A8028292BC678A2F3B03A20DCF660646`

## 3. Bản Blender palette

Bản làm việc duy nhất đã đổi material:

`blender files/Before Baking - Grounded Pastel Test.blend`

File gốc `blender files/Before Baking.blend` không đổi.

### Material mapping để review

| Original material | New color | Hex |
| --- | --- | --- |
| Room | Warm Cream / Mist Gray | `#F1E9DE` / `#DCE2DE` |
| Backdrop | Mist Gray / Soft Sage | `#DCE2DE` / `#B8C9BD` |
| Base White | Warm Cream | `#F1E9DE` |
| Base Gray | Mist Gray | `#DCE2DE` |
| Base Purple | Deep Sage | `#405D52` |
| Base Blue | Dusty Blue | `#8FA9B8` |
| Base Blue Two | Dusty Blue | `#8FA9B8` |
| Base Blue.001 | Dusty Blue | `#8FA9B8` |
| Chair Cushion | Sage | `#718E7A` |
| Computer | Dusty Blue | `#8FA9B8` |
| Drawer | Mist Gray | `#DCE2DE` |
| Drawer Shelves | Sage | `#718E7A` |
| Desk Pad | Soft Terracotta | `#D99478` |
| Keyboard | Warm Cream | `#F1E9DE` |
| Welcome Mat | Deep Sage / Sage | `#405D52` / `#718E7A` |
| Piano Stand | Deep Sage | `#405D52` |
| Speaker | Dusty Blue | `#8FA9B8` |
| Paper | Soft Terracotta | `#D99478` |
| Book Cover One | Dusty Blue | `#8FA9B8` |
| Book Cover Two | Soft Terracotta | `#D99478` |
| Book Cover Four | Sage | `#718E7A` |
| Flower Center | Muted Yellow | `#D8BA68` |
| Flower Center Two | Dusty Rose | `#D6A0A0` |
| Another Flower / Daylily / Lily | Dusty Rose | `#D6A0A0` |
| Plant Gradient / Hanging Plant / Plant Stem | Deep Sage / Sage | `#405D52` / `#718E7A` |
| Stone wall | Mist Gray, giữ moss hiện có | `#DCE2DE` |
| Wood / Light Wooden | Gỗ tự nhiên hiện có | Không đổi |

Phân bổ chủ đích:

- 60% neutral và natural wood: Room, Backdrop, Base White, Base Gray, Drawer, Keyboard và gỗ.
- 25% Sage/Dusty Blue: chair, computer, shelves, speaker, book cover và cây.
- 10% Terracotta/peach: desk pad, paper và một nhóm book cover.
- 5% accent nhỏ: Muted Yellow, Dusty Rose và các pastel nhỏ hiện có.

Không biến toàn bộ object hồng thành sage. Các furniture lớn được chia giữa cream, gray, sage, dusty blue và terracotta.

### Kiểm tra bảo toàn

Geometry + UV signature trước và sau palette:

`f166e359e1deb4459a74045abc66ceb237da26428d62b3518dad57491ba26a5a`

Kết quả:

- Geometry đổi: Không.
- UV đổi: Không.
- Object name đổi: Không.
- GLB structure đổi: Không.
- Raycaster/animation đổi bởi phase này: Không.

## 4. Kết quả test bake Day atlas số 1

### Cấu hình test

- Atlas: First Day only.
- Resolution: 4096×4096.
- UV: layer `SimpleBake` hiện có trên merged target `First`.
- Material grouping: 24 source object của `FinalFirst_Baked` / First Texture Set.
- Margin: 16 px, `EXTEND`.
- Samples: 50, lấy từ `boosted_sample_count` đã lưu của SimpleBake.
- Pass: Cycles `COMBINED`, Direct + Indirect + Color.
- Cách bake: native Cycles selected-to-active vào merged target `First`.
- Output: PNG 16-bit RGBA trong thư mục artifact; không ghi vào `public/textures`.
- Thời gian: `01:04:57.468`, dài hơn log SimpleBake cũ khoảng 48 lần.

File test:

- `artifacts/grounded-pastel-test/first-texture-set-day-test.png`
- `artifacts/grounded-pastel-test/first-day-test-bake.blend`
- `artifacts/grounded-pastel-test/first-day-atlas-comparison.png`

SHA-256:

- PNG test: `E9B79B5FD313AE944BE59ED6C79E5BD46137BAE2B2214B3E060472F974F9F9AF`
- Workspace test: `A0C0333C54AD4FC6754DC5AA1A6A09C2D0101179B37FAE594D9641C3C7E485A7`

Geometry + UV signature của source trước/sau test bake vẫn giống nhau:

`fd0a36269ad9f82241a0ca424e281fb611845cf7be8ced2c71887b5fed7afaf8`

### So sánh định lượng

| Tiêu chí | Atlas production hiện tại | Native Cycles test | Kết luận |
| --- | ---: | ---: | --- |
| Kích thước | 4096×4096 | 4096×4096 | Đạt |
| Black pixels | 10.20% | 28.27% | Không đạt |
| Dark pixels | 15.80% | 35.31% | Không đạt |
| Median luminance | 94.00 | 65.92 | Không đạt |
| Alpha zero | 0% / RGB production | 9.08% | Không đạt |
| Alpha partial | 0% | 0% | Không có alpha mềm |
| Alpha opaque | 100% ở PNG nguồn cũ | 90.92% | Không đạt |

### Đánh giá theo checklist

| Hạng mục | Kết quả | Ghi chú |
| --- | --- | --- |
| UV alignment | Đạt về cấu trúc | Dùng chính merged target `First` và UV `SimpleBake`; vị trí island tổng thể khớp atlas hiện tại. |
| Lighting | Không đạt | Midtone thấp hơn rõ rệt; không thể coi là tương đương workflow cũ. |
| Shadows | Không đạt | Vùng đen/tối tăng mạnh; nhiều ray/projection miss. |
| Gamma / color space | Không đạt | Highlight gần tương đương nhưng median luminance giảm từ 94.00 xuống 65.92. |
| Seams | Không đạt | Có nhiều khoảng checkerboard/transparent lớn giữa và trong các island. |
| Missing materials / coverage | Không đạt | Source group đủ 24 object, nhưng native selected-to-active không phủ kín merged target. |
| Transparency | Không đạt | Atlas cũ opaque; test có 9.08% alpha bằng 0. |
| Texture bleeding | Chưa thấy bleeding chéo island rõ | Không thể phê duyệt vì coverage/seam đã thất bại trước. |

**Kết luận test bake: FAIL. Không dùng file này làm production và không bake bảy atlas còn lại.**

## 5. Khác biệt so với workflow SimpleBake gốc

1. SimpleBake addon không có trong Blender hiện tại, nên không thể chạy đúng operator/pipeline gốc.
2. SimpleBake cũ dùng `global_mode`, `merged_bake`, `copy_and_apply` và cơ chế copy/apply riêng của addon. Native test dùng Cycles selected-to-active trên merged target; hai cơ chế không tương đương.
3. Object `Plane.003` vẫn thuộc atlas First trong `For Export.blend`, nhưng không còn trong `Before Baking.blend`. Bản chính xác còn trong `For Night Time Baking.blend` với material `Wood`; test chỉ append object này vào workspace tạm để đủ 24 source. Không sửa source Day production.
4. SimpleBake lưu cấu hình 4096, 50 samples, internal float và output 16-bit. Native test giữ resolution/samples/margin nhưng dùng pipeline lưu PNG của Blender với AgX; color-management path có thể khác addon.
5. PNG nguồn cũ opaque 100% và WebP production là RGB. Native output là RGBA với 9.08% transparent.
6. Log SimpleBake cũ ghi khoảng 81 giây; native Cycles test mất gần 65 phút trong môi trường hiện tại.
7. Native bake có ray/projection misses lớn, nên không thể giả định kết quả COMBINED giống SimpleBake.

## 6. UI palette đã cập nhật

Light UI dùng đúng bảng màu:

| Token | Hex |
| --- | --- |
| Deep Sage | `#405D52` |
| Sage | `#718E7A` |
| Soft Sage | `#B8C9BD` |
| Warm Cream | `#F1E9DE` |
| Mist Gray | `#DCE2DE` |
| Text | `#202522` |

Đã cập nhật:

- `src/style.scss`
- `src/styles/variables.scss`
- Các màu hardcode liên quan đến scene/loading trong `src/main.js`

Layout và animation không bị thay đổi bởi phase palette UI. Facebook, glass, water và shader cây không bị ép sang sage.

Dark UI được chuyển khỏi tím cũ sang charcoal/deep-sage/cream tương ứng để không còn xung đột palette khi đổi theme.

## 7. File đã tạo hoặc chỉnh trong staged workflow

### Source chỉnh sửa

- `src/shaders/theme/fragment.glsl`
- `src/main.js` — chỉ phần shader uniform tạm và màu scene/loading thuộc scope này.
- `src/style.scss` — palette/theme colors.
- `src/styles/variables.scss` — palette variables.

### Blender và tài liệu

- `blender files/Before Baking - Grounded Pastel Test.blend`
- `docs/grounded-pastel-color-audit.md`
- `docs/grounded-pastel-material-mapping.md`
- `docs/grounded-pastel-phase1-review.md`

### Script kiểm soát và kiểm tra

- `scripts/blender/apply_grounded_pastel_palette.py`
- `scripts/blender/bake_first_day_test_atlas.py`
- `scripts/blender/inspect_bake_source_match.py`
- `scripts/analyze_grounded_pastel_test_atlas.py`

### Backup và artifact

- `backups/grounded-pastel-phase1-2026-09-01/`
- `artifacts/grounded-pastel-test/`

`dist/` được Vite build lại để kiểm tra nhưng là generated/ignored output.

Repository đã có các thay đổi khác từ trước staged workflow này. Các file ngoài danh sách trên không được xem là thay đổi của phase Grounded Pastel hiện tại.

## 8. Xác minh cuối

- `npm run build`: Pass.
- Cảnh báo còn lại: `eval` có sẵn trong `src/main.js` và bundle lớn hơn 500 kB; không phải lỗi build của palette.
- 8 texture production: Không đổi.
- 3 Blender production source: Không đổi.
- Remaining seven atlas: Chưa bake.
- Production GLB: Không đổi.

## Điểm cần bạn phê duyệt sau này

Không nên bake tiếp bằng script native hiện tại. Bước tiếp theo an toàn là một trong hai hướng:

1. Cài/khôi phục đúng SimpleBake phiên bản tương thích và chạy lại **một** atlas test.
2. Điều tra lại quy trình merged target/cage/source matching của native Cycles cho tới khi atlas First test đạt đủ coverage, opaque output và độ sáng gần atlas gốc.

Chỉ sau khi một atlas test mới đạt mới nên xin phê duyệt bake bảy atlas còn lại.
