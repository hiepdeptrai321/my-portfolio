# Xbox controller integration

Ngày cập nhật: 2026-09-03  
Trạng thái: **Hoàn tất — Blender verification và production build đều pass**

## Kết quả trong Blender

- File nguồn cuối: [`My Room - FINAL.blend`](../blender%20files/My%20Room%20-%20FINAL.blend).
- Object được đổi tên thành `Xbox_Controller_Raycaster_Hover`.
- Controller được tháo khỏi hierarchy import, dựng thẳng và hướng mặt ra ngoài.
- Vị trí: `[-2.934394, -0.841689, 4.858981]`.
- Rotation: `[0, 0, 0]`.
- Kích thước: `[0.350247, 0.542234, 0.305998]`.
- Đáy controller cách mặt trên của `Plane.041_Baked` đúng `0.003` đơn vị, không còn xuyên vào kệ.
- Texture gốc được giữ, bao gồm màu của các nút ABXY.

## Material

Material được đổi tên thành `Xbox_Controller_Material` và chuẩn hóa:

| Thuộc tính | Giá trị |
| --- | ---: |
| Metallic | `0.00` |
| Roughness | `0.68` |
| IOR | `1.46` |
| Specular IOR Level | `0.28` |
| Coat Weight | `0.08` |
| Coat Roughness | `0.35` |

Giá trị IOR lỗi từ bản import (`1000`) đã được thay bằng giá trị nhựa hợp lý. Base-color image vẫn được pack trong `.blend`.

## Cleanup

- Xóa model giá đỡ đôi nằm ngoài phòng: `Object_2`, `Object_3`, `Object_4`, `Object_5.001`, `Object_6` và root `stand_fore_controller_Xbox.obj.cleaner.materialmerger.gles`.
- Xóa `61` Empty wrapper không còn sử dụng.
- Giữ lại `RootNode` vì đây là parent hợp lệ của cây ngoài cửa sổ.
- Khôi phục tên semantic `LinkedIn_Fourth_Raycaster_Pointer_Hover` trước khi cleanup.
- Không còn tên import cũ `Object_5` hoặc model stand trong file cuối.

## Model web và tương tác

- Model: [`xbox-controller.glb`](../public/models/xbox-controller.glb).
- GLB chỉ chứa một mesh, một material và một base-color image.
- Draco compression: bật, level `6`.
- Kích thước: `309,440` bytes.
- SHA-256: `9D2994E3829541BC3BBF3D3476E43703A6BD18257A24F2BC287876321FAFE5AD`.
- Controller dùng shader Grounded Pastel tự tạo shading mềm, không phụ thuộc vào đèn PBR riêng.
- Hover scale: `1.12×`.
- Hover lift: `0.08` đơn vị.
- Intro: controller xuất hiện sau Facebook theo cùng animation pop-in của nhóm thẻ profile.
- Raycaster chỉ được bật sau khi intro của controller hoàn tất.
- Vỏ controller dùng Deep Sage `#405D52` và Mist Gray `#DCE2DE`; hover chuyển sang Sage `#718E7A` và Warm Cream `#F1E9DE`.
- Chi tiết màu của các nút Xbox trong texture gốc được giữ lại.
- Khung ảnh cũ `Frame_3_Second_Raycaster_Hover` được ẩn và loại khỏi raycaster để không chồng lên controller.
- Controller không có click action và không đổi con trỏ thành pointer.

## Xác minh

- Blender verification: Pass.
- `165` mesh tổng cộng: `161` baked room + LinkedIn + Facebook + Tree + Xbox Controller.
- Chỉ còn một Empty hợp lệ: `RootNode`.
- Obsolete social objects: `0`.
- Obsolete controller imports: `0`.
- Missing external images: `0`.
- `npm run build`: Pass với Vite `6.4.3`.
- Dev server trả HTTP `200` cho trang chính, `src/main.js` và `xbox-controller.glb`.
- Production JS: `dist/assets/index-D70fKXIz.js`.
- SHA-256 production JS: `60D54212F3A93D5C89F0CDD1FE6CE6E43FE64D55DEDE624EE606F5F2887652E2`.
- `public/models/xbox-controller.glb` và `dist/models/xbox-controller.glb` có cùng SHA-256.

## Preview

- [Front view](../artifacts/xbox-controller-audit/xbox-room-front.png)
- [Perspective view](../artifacts/xbox-controller-audit/xbox-room-perspective.png)

## File thay đổi chính

- [`My Room - FINAL.blend`](../blender%20files/My%20Room%20-%20FINAL.blend)
- [`src/main.js`](../src/main.js)
- [`xbox-controller.glb`](../public/models/xbox-controller.glb)
- [`prepare_xbox_controller.py`](../scripts/blender/prepare_xbox_controller.py)
- [`verify_final_room_blend.py`](../scripts/blender/verify_final_room_blend.py)
