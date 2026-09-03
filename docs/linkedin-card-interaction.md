# LinkedIn card interaction

Ngày cập nhật: 2026-09-03  
Trạng thái: **HOÀN TẤT — BUILD PASS**

## Kết quả

Thẻ YouTube cũ được ẩn khỏi runtime và không còn tạo hitbox. Thẻ LinkedIn mới được tải độc lập, có intro, hover và click tương tự Facebook.

## Object và model

- Object trong Blender: `LinkedIn_Fourth_Raycaster_Pointer_Hover`.
- Model web: [`linkedin-card.glb`](../public/models/linkedin-card.glb).
- Vị trí world: `[-2.543337, 3.958757, 5.613009]`.
- Kích thước hiển thị: `[0.588526, 0.111991, 0.606582]`.
- Materials: `Tinta_1.002`, `Tinta_3.001`, `Tinta_3.002`.
- GLB chỉ chứa một mesh và không có texture ngoài.
- Kích thước GLB: `881,780` bytes.
- SHA-256: `49041036A3C580A0B021C8DC978724C9E034499AE40E07E62F0D4CE313E18C0B`.

## Hành vi đã thêm

- Xuất hiện lần lượt trong intro cùng nhóm social: Boba → LinkedIn → GitHub → Facebook.
- Hitbox chỉ được kích hoạt sau khi LinkedIn xuất hiện xong.
- Hover phóng to `1.4×`.
- Hover nghiêng quanh cạnh dưới giống Facebook.
- Màu xanh và trắng chuyển sáng mượt trong `0.25s`, trở về màu nghỉ trong `0.3s`.
- Click mở `https://www.linkedin.com/in/dophuhiep212/` trong tab mới với `noopener,noreferrer`.
- YouTube cũ bị ẩn và thoát sớm trước bước material/hitbox.

## Căn lại ba thẻ social

GitHub trong `room-main.glb` cũ vẫn ở slot bên trái (`x = -2.309550`), nên bị LinkedIn mới che. Runtime hiện chuyển GitHub sang tọa độ giữa đã author trong Blender: `x = -1.657146`.

| Thẻ | Min X | Max X | Khoảng hở tới thẻ kế tiếp |
| --- | ---: | ---: | ---: |
| LinkedIn | -2.543689 | -1.955163 | 0.025189 |
| GitHub | -1.929974 | -1.399472 | 0.024171 |
| Facebook | -1.375301 | -0.795589 | — |

Ba thẻ hiện theo đúng thứ tự trái → phải: **LinkedIn → GitHub → Facebook**. GitHub được di chuyển trước khi lưu initial transform và tạo hitbox, nên intro, hover và click đều dùng đúng vị trí giữa.

## Palette social card

| Thành phần | Rest | Hover |
| --- | --- | --- |
| Blue | `#455A86` | `#576F9E` |
| White | `#DED8D4` | `#F0E8E3` |

Facebook tiếp tục dùng cùng palette và animation như trước.

## Blender cleanup

- Đổi tên mesh hiển thị từ `Objeto_1_Tinta (1)_0` thành tên semantic LinkedIn.
- Giữ nguyên world transform trước và sau khi bỏ parent.
- Xóa hai mesh nhập thừa ở world origin.
- Xóa `51` Empty wrapper không còn được sử dụng.
- File cuối còn `166` mesh: `163` baked room + Facebook + LinkedIn + Tree.
- Không có object Twitter/YouTube và không thiếu texture ngoài.
- Verification Blender: `Pass`.

## Build verification

- `npm run build`: Pass với Vite `6.4.3`.
- `public/models/linkedin-card.glb` và `dist/models/linkedin-card.glb` có cùng SHA-256.
- Bundle production chứa model URL, LinkedIn profile URL và các nhánh interaction LinkedIn.
- Cảnh báo `eval` và chunk lớn là cảnh báo đã tồn tại, không phát sinh từ thẻ LinkedIn và không chặn build.
- Không thể thực hiện lượt rê chuột trực quan tự động vì phiên làm việc không có trình duyệt điều khiển khả dụng.

## File chính đã thay đổi

- [`src/main.js`](../src/main.js)
- [`My Room - FINAL.blend`](../blender%20files/My%20Room%20-%20FINAL.blend)
- [`linkedin-card.glb`](../public/models/linkedin-card.glb)
- [`prepare_linkedin_card.py`](../scripts/blender/prepare_linkedin_card.py)
- [`verify_final_room_blend.py`](../scripts/blender/verify_final_room_blend.py)
