# SimpleBake restoration audit — Option A

Ngày kiểm tra: 2026-09-02  
Trạng thái: **DỪNG TẠI PHASE A4 — CHƯA CÀI ADDON, KHÔNG BAKE**

> **Official SimpleBake ZIP is required.**

Không có texture production, Blender source production, GLB, UV, object name, shader, raycaster, interaction hoặc animation nào bị sửa trong quá trình kiểm tra này.

## Kết luận

1. Dấu vết trong `.blend` khớp với addon thương mại chính thức **“SimpleBake - Simple PBR and other baking in Blender”** của **HaughtyGrayAlien**, phân phối qua Superhive/former Blender Market.
2. Blender hiện tại là **Blender 5.2.1 LTS**, official Windows x64 Release build, không phải alpha/beta/RC/custom build.
3. Blender 5.2.1 nằm trong phạm vi hỗ trợ chính thức của SimpleBake Blender 5 Edition.
4. Không tìm thấy cài đặt SimpleBake cũ, thư mục trùng lặp, preference remnant hoặc mixed-version files.
5. Không tìm thấy ZIP SimpleBake chính thức ở các vị trí cục bộ đã kiểm tra.
6. Vì ZIP chính thức không tồn tại, không được phép cài addon, enable addon hoặc tiếp tục tới A5–A7.
7. Grounded Pastel working copy vẫn còn material và signature bảo toàn, nhưng **chưa sẵn sàng bake** vì addon chưa được cài và atlas membership hiện có một số tên object không còn khớp source Day.

## A1 — Nhận diện đúng SimpleBake

### Identifier tìm thấy trong `.blend`

Các chuỗi được đọc trực tiếp từ file Blender:

- Module/folder: `SimpleBake`
- Panel class: `SIMPLEBAKE_PT_main_panel`
- UI list classes:
  - `SIMPLEBAKE_UL_Presets_List`
  - `SIMPLEBAKE_UL_Local_Presets_List`
  - `SIMPLEBAKE_UL_Objects_List`
- Scene property group: `SimpleBake_Props`
- Custom data keys:
  - `SB_uv_used_for_bake`
  - `SB_copy_and_apply_from`
  - `SB_bake_operation_id`
  - `SB_orig_fake_user`
- UV layer convention: `SimpleBake`
- Output collection/path convention: `SimpleBake_Bakes` / `//SimpleBake_Bakes`
- Resource path của máy tác giả gốc được nhúng trong `.blend`:

```text
C:\Users\andre\AppData\Roaming\Blender Foundation\Blender\4.3\scripts\addons\SimpleBake\resources\copy_and_apply_mats.blend
```

File gốc lưu Blender data version `4.3.32`, phù hợp với đường dẫn addon Blender 4.3 nói trên.

### Đối chiếu danh tính

Các identifier và feature lưu trong file — Merged Bake, Copy and Apply, existing `SimpleBake` UV, CyclesBake, presets và `SimpleBake_Bakes` — khớp với feature của sản phẩm chính thức trên [Superhive](https://superhivemarket.com/products/simplebake---simple-pbr-and-other-baking-in-blender-2).

Đây không phải addon GitHub trùng tên được tìm thấy trên mạng. Không có addon thay thế nào được tải hoặc cài.

Kết luận identity: **Confirmed với độ tin cậy cao là official Superhive SimpleBake implementation**.

Không thể suy ra chính xác version lịch sử đã dùng để tạo file chỉ từ `.blend`; addon version number không được lưu trong metadata đã tìm thấy.

## A2 — Blender và compatibility

### Blender hiện tại

| Thuộc tính | Giá trị |
| --- | --- |
| Version | `5.2.1 LTS` |
| Build date | `2026-08-25` |
| Build hash | `9e2066aef7ef` |
| Build branch | `blender-v5.2-release` |
| Build type | `Release` |
| Version cycle | `release` |
| Platform | Windows x64 |
| Executable | `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` |
| Python | `3.13.13` |

Blender Foundation xác nhận 5.2.1 là bản LTS chính thức phát hành ngày 25-08-2026: [Blender 5.2 LTS](https://www.blender.org/releases/5-2/).

### SimpleBake compatibility

Trang chính thức của SimpleBake ghi:

- Blender compatibility: `5.0 - 5.2`.
- Chỉ hỗ trợ official releases; modified build, beta, alpha và release candidate không được hỗ trợ.

Nguồn: [SimpleBake trên Superhive](https://superhivemarket.com/products/simplebake---simple-pbr-and-other-baking-in-blender-2).

Release notes chính thức hiện ghi latest Blender 5 Edition là **2.9.11 — 25-08-2026**. Version 2.8.5 đã bổ sung color-space defaults riêng cho Blender 5.2+: [SimpleBake release notes](https://www.toohey.co.uk/SimpleBake/releasenotes4.html).

Kết luận compatibility: **Blender 5.2.1 LTS hiện tại được hỗ trợ; không có bằng chứng cần downgrade Blender.**

## A3 — Kiểm tra cài đặt cũ/xung đột

### Blender user config

- Config root: `C:\Users\hiepdeptrai\AppData\Roaming\Blender Foundation\Blender\5.2`
- `scripts/`: không tồn tại.
- `extensions/`: không tồn tại.
- `userpref.blend`: không chứa chuỗi SimpleBake.
- Enabled addons: chỉ có các module Blender/Core; không có `SimpleBake`.
- System `addons_core`: không có SimpleBake.

### Kết quả tìm remnants

- Old SimpleBake folder: Không tìm thấy.
- Duplicate SimpleBake module: Không tìm thấy.
- Pre-Blender-4 remnants: Không tìm thấy.
- Disabled-but-installed SimpleBake: Không tìm thấy.
- Mixed-version files: Không tìm thấy.

Không có gì cần backup hoặc xóa. Blender preferences và các addon khác không bị sửa.

## A4 — Tìm ZIP chính thức

Các vị trí đã kiểm tra read-only:

- `C:\Users\hiepdeptrai\Downloads`
- `C:\Users\hiepdeptrai\Desktop`
- `C:\Users\hiepdeptrai\Documents`
- Blender user config
- Toàn bộ project hiện tại

Kết quả:

- File/folder có tên SimpleBake: `0`.
- ZIP đã rà soát theo nội dung: `49`.
- ZIP chứa `SimpleBake`, `SIMPLEBAKE_PT_main_panel` hoặc `copy_and_apply_mats.blend`: `0`.
- ZIP lỗi/không đọc được: `0`.

### Yêu cầu để tiếp tục

> **Official SimpleBake ZIP is required.**

ZIP phải được tải hợp pháp từ trang chính thức:

- [SimpleBake - Simple PBR and other baking in Blender — Superhive](https://superhivemarket.com/products/simplebake---simple-pbr-and-other-baking-in-blender-2)

Nên cung cấp bản **Blender 5 Edition 2.9.11 hoặc bản mới hơn mà Superhive ghi tương thích Blender 5.2**.

Không tải cracked copy, unofficial mirror hoặc addon GitHub trùng tên. Không cung cấp password, account secret hoặc license key; chỉ cần đặt ZIP hợp lệ vào `Downloads` hoặc một thư mục trong project rồi yêu cầu kiểm tra lại.

## Trạng thái A5 — Installation

| Hạng mục | Trạng thái |
| --- | --- |
| Installed SimpleBake version | Không có |
| Installation path | Không có |
| Addon enabled | Không |
| Preferences saved | Không thay đổi |
| Restart performed | Không cần |
| Import/Python error validation | Chưa thể chạy |

Expected legacy addon location sau khi cài đúng ZIP có khả năng là:

```text
C:\Users\hiepdeptrai\AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons\SimpleBake
```

Đường dẫn thực tế phải được xác nhận từ metadata của ZIP chính thức; chưa tạo thư mục này.

## Metadata bake đã recover read-only

Đây là dữ liệu còn lưu trong `Before Baking.blend`; chưa phải xác nhận từ panel của addon đang hoạt động.

| Setting | Giá trị lưu |
| --- | --- |
| Render engine | Cycles |
| Evidence bake type | CyclesBake `COMBINED` |
| `global_mode` | `1` raw enum |
| Atlas input/output | 4096×4096 |
| Blender bake margin | 16 px, `ADJACENT_FACES` |
| UV pack margin | `0.03` |
| Unwrap margin | `0.03` |
| Cycles render samples | `256` |
| SimpleBake boosted sample count | `50` |
| Scene device intent | `GPU` |
| Current Cycles compute backend | `NONE` trong user preferences |
| Detected GPU | NVIDIA GeForce RTX 3060, CUDA và OptiX device rows |
| Merged bake | Enabled |
| Merged bake name | `MergedBake` |
| Copy and Apply | Enabled |
| Hide source objects | Enabled |
| Apply bakes to originals | Disabled |
| Preserve original materials | Disabled |
| Prefer existing `SimpleBake` UV | Enabled |
| Generate/new UV raw option | `0` |
| Restore original UV | Disabled |
| Selected-to-active | Disabled |
| Cycles selected-to-active | Disabled |
| Target object | None |
| Ray distance | `0.0` |
| Stored cage extrusion | `0.1` |
| Clear image before bake | Enabled |
| Internal float | 32-bit enabled |
| Export depth | 16-bit enabled |
| Alpha | Enabled |
| External auto-save | Disabled |
| Stored export path | `//SimpleBake_Bakes` |
| Background bake | Disabled |
| Saved preset | `Default 4k` |
| Saved foreground result | 81 seconds, 100% complete |

Lưu ý quan trọng về samples: [FAQ chính thức](https://superhivemarket.com/products/simplebake---simple-pbr-and-other-baking-in-blender-2/faq) nói CyclesBake sử dụng render sample count. Vì vậy `256` có khả năng là samples của COMBINED bake; `boosted_sample_count=50` không được tự động dùng thay thế cho test tiếp theo trước khi panel chính thức xác nhận.

### Device chưa được xác nhận hoàn chỉnh

Scene lưu `GPU`, nhưng current Cycles preference có `compute_device_type=NONE`. RTX 3060 xuất hiện dưới CUDA và OptiX; SimpleBake release notes/FAQ cảnh báo OptiX baking không ổn định và addon chặn OptiX theo mặc định.

Không tự đổi sang CUDA/CPU ở phase này. Device phải được SimpleBake health check xác nhận sau khi cài.

## Atlas setup đã recover từ `For Export.blend`

`SimpleBake_Bakes` chứa đúng 166 baked object, chia theo baked material:

| Atlas | Baked material | Số object | Merged target | UV | Image node target hiện lưu |
| --- | --- | ---: | --- | --- | --- |
| First | `FinalFirst_Baked` | 24 | `First` | `SimpleBake` | `//first_texture_set_day.png` |
| Second | `RealFinalSecond_Baked` | 5 | `Second` | `SimpleBake` | `//second_texture_set_day.png` |
| Third | `FinalThird_Baked` | 33 | `Third` | `SimpleBake` | `//third_texture_set_day.png` |
| Fourth | `FinalFourth_Baked` | 104 | `Fourth` | `SimpleBake` | `//fourth_texture_set_day.png` |

Tuy nhiên `SimpleBake_Props.objects_list` trong `Before Baking.blend` hiện chỉ chứa:

```text
Cube
```

Do đó addon chưa thể được giả định sẽ tự khôi phục đủ bốn group từ panel. Group membership phải được đối chiếu lại sau khi addon hoạt động.

### Source membership discrepancy

So sánh tên object bake cũ với `Before Baking.blend` và Grounded Pastel copy:

| Atlas | Expected | Present trong Day/Grounded | Missing names |
| --- | ---: | ---: | --- |
| First | 24 | 23 | `Plane.003` |
| Second | 5 | 4 | `Backdrop` |
| Third | 33 | 30 | `Kirby`, `Plane.004`, `Plane.006` |
| Fourth | 104 | 103 | `Plane.002` |

`For Night Time Baking.blend` có đủ Second/Third/Fourth, nhưng First thiếu `Cube.027` và có `Plane.003`. Không trộn source Day/Night hoặc tự đổi tên object ở phase này.

Đây là lý do thứ hai khiến Grounded Pastel copy chưa thể được đánh dấu ready-to-bake.

## Texture/material preflight read-only

### `Before Baking.blend` và Grounded Pastel copy

- 73/73 materials dùng nodes.
- Không có material thiếu Surface output link.
- Không có Image Texture node rỗng.
- Tất cả external source image cần thiết đều đã packed trong `.blend`.
- Không phát hiện missing texture dependency trong hai source này.
- 176 mesh object; `Vert` và `Vert.001` không có UV và cần SimpleBake Health Check xác định có thuộc bake list hay không.

### `For Export.blend`

- `Desktop.png` và `kirbyface.jpg` resolve được.
- 22 external references không resolve tại filepath đang lưu.
- Bốn atlas PNG hiện nằm trong `blender files/textures/`, nhưng material nodes trong `For Export.blend` trỏ tới `blender files/` root nên đang báo missing.
- Các historic EXR bake outputs, `autumn_field_4k.hdr` và bốn `Wood02_*.tga` cũng đang missing theo path lưu.

Không relink hoặc sửa filepath ở phase này.

## Grounded Pastel working copy

File:

`blender files/Before Baking - Grounded Pastel Test.blend`

Đã xác nhận:

- Marker `grounded_pastel_palette` còn tồn tại.
- Geometry/UV signature còn tồn tại:

```text
f166e359e1deb4459a74045abc66ceb237da26428d62b3518dad57491ba26a5a
```

- Material node graph hợp lệ theo preflight read-only.
- Packed source textures còn đầy đủ.

Ready to bake: **No**.

Lý do:

1. Official SimpleBake chưa được cài/enabled.
2. SimpleBake panel và Health Check chưa thể chạy.
3. Saved object list chỉ còn `Cube`.
4. Sáu tên object từ atlas Day cũ không còn khớp Day/Grounded source.
5. GPU backend chưa được xác nhận.

## Proposed FIRST test bake — provisional only

Không được chạy cho tới khi ZIP chính thức được cung cấp, addon enable thành công và các discrepancy bên trên được xử lý trên một copy.

| Setting | Proposed value cần xác nhận trong SimpleBake panel |
| --- | --- |
| Source | Copy của `Before Baking - Grounded Pastel Test.blend` |
| Scope | ONE Day atlas only: First |
| Addon | Official SimpleBake Blender 5 Edition 2.9.11 hoặc compatible newer |
| Bake mode | CyclesBake |
| Bake type | COMBINED |
| Multiple objects to one texture set / merged bake | Enabled |
| Expected First membership | 24 objects, sau khi xác minh `Plane.003` đúng nguồn |
| Resolution | 4096×4096 |
| UV | Existing original workflow; prefer `SimpleBake` UV, không tạo/đổi UV thủ công |
| Bake margin | 16 px |
| UV pack/unwrap margin | 0.03 / 0.03 nếu panel restore đúng |
| Cycles render samples | 256, cần panel xác nhận |
| Selected-to-active | Disabled |
| Target/cage | None; ray distance 0; không dùng native fallback projection |
| Copy and Apply | Enabled trên test copy |
| Apply to originals | Disabled |
| Clear image | Enabled |
| Internal/export depth | 32-bit float internal / 16-bit export |
| Output | Temporary non-production path; không ghi vào 8 WebP production |
| Device | Chưa chốt; SimpleBake Health Check phải chọn supported CPU/CUDA, không OptiX mặc định |

Đây chưa phải setting được duyệt để chạy. Sau khi cài addon hợp lệ, cần thực hiện A5–A7, chụp/đọc panel state và xuất report mới trước khi bake.

## Thay đổi đã thực hiện trong audit này

Chỉ tạo các file audit trong workspace:

- `scripts/blender/audit_simplebake_restore.py`
- `scripts/blender/inspect_simplebake_atlas_membership.py`
- `docs/simplebake-restoration-audit.md`

Không xóa/copy/install bất kỳ addon nào. Không lưu lại bất kỳ `.blend` production nào.
