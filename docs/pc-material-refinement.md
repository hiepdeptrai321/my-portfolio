# PC material refinement

Ngày hoàn tất: 2026-09-03  
Trạng thái: **Hoàn tất**

## Kết quả

Chỉ khu vực PC được tinh chỉnh. Hình dáng, kích thước, vị trí PC, camera, bố cục phòng và các vật trang trí khác được giữ nguyên.

- Vỏ trắng gắt được thay bằng warm off-white `#DDD8D4`.
- Các phần phụ của vỏ dùng soft light gray `#C9C8C6` để tạo độ tách khối nhẹ.
- Đã loại bỏ nguyên nhân tạo vệt xanh loang: PC xanh cũ nằm trong mesh atlas `Fourth` không còn được render chồng với PC mới.
- Vật liệu vỏ dùng màu phẳng sạch và có highlight bóng nhẹ; không dùng texture noise hay hiệu ứng painterly.
- Kính hông dùng tint xanh xám/lavender rất nhạt `#D9CBE5`, transmission `0.82`, opacity `0.16`, roughness `0.12`.
- Các chi tiết stylized bên trong được giữ lại với mauve, plum và lavender dịu.
- LED lavender `#D8B5EE` vẫn được giữ, nhưng ambient glow đã giảm opacity từ `0.32` xuống `0.25` để ánh sáng kín đáo hơn.
- Đèn lavender trong PC giảm energy từ `55` xuống `42`.
- Chế độ Day/Night vẫn đổi màu PC đồng bộ trong `1.5s`.

## Cách xử lý vệt xanh

`room-main.glb` chứa PC xanh cũ bên trong mesh gộp `Fourth`. Bản trước chỉ đặt một lớp màu mới lên trên nên các mép cũ có thể lộ ra và xảy ra z-fighting.

Bản sửa hiện tại:

1. Loại các tam giác của PC cũ khỏi `Fourth` tại runtime.
2. Ẩn các helper `Computer_Fan_*` và `Computer_Glass` cũ.
3. Dùng `pc-upgrade.glb` làm model PC thay thế hoàn chỉnh, không còn là lớp phủ.

Kiểm tra vùng loại bỏ trên `room-main.glb`:

- Tổng tam giác của `Fourth`: `64,248`.
- Tam giác thuộc vùng PC cũ được loại bỏ: `5,236`.
- Tam giác còn lại: `59,012`.
- Tỷ lệ vùng chỉnh: `8.1497%`.

Room atlas và `room-main.glb` không bị ghi đè.

## Bảng màu PC

| Thành phần | Màu | Hex |
| --- | --- | --- |
| Vỏ chính | Warm Off-White | `#DDD8D4` |
| Trim/vỏ phụ | Soft Light Gray | `#C9C8C6` |
| Kính | Faint Cool Lavender Gray | `#D9CBE5` |
| Nội thất trung tính | Mauve Gray | `#8F8193` |
| GPU | Muted Plum | `#74617F` |
| Motherboard | Mauve | `#A582A4` |
| Chi tiết nhỏ | Soft Lavender | `#BBA8CC` |
| Fan accents | Pastel Lilac | `#CBB3DB` |
| LED | Pastel Lavender | `#D8B5EE` |

## File đã cập nhật

- [My Room - FINAL.blend](../blender%20files/My%20Room%20-%20FINAL.blend)
- [pc-upgrade.glb](../public/models/pc-upgrade.glb)
- [src/main.js](../src/main.js)
- [PC fragment shader](../src/shaders/pc/fragment.glsl)
- [PC vertex shader](../src/shaders/pc/vertex.glsl)
- [upgrade_pc_area.py](../scripts/blender/upgrade_pc_area.py)
- [audit_room_pc_removal.py](../scripts/blender/audit_room_pc_removal.py)
- [verify_final_room_blend.py](../scripts/blender/verify_final_room_blend.py)

## Xác minh

- Blender verification: **Pass**, không có lỗi.
- Final Blender: `184` objects, `181` meshes.
- Geometry case được giữ nguyên: `2,904` vertices, `2,439` polygons.
- Missing external images: `0`.
- `pc-upgrade.glb`: `17` meshes, `10` materials, `89,744` bytes.
- `npm run build`: **Pass** với Vite `6.4.3`.
- Production output: `dist/assets/index-rzzgHTrW.js` và `dist/assets/index-y74iNUV2.css`.
- Trang chính, `src/main.js`, model PC và hai PC shader đều trả HTTP `200` trên dev server.

SHA-256:

- `My Room - FINAL.blend`: `75CEBCDE44CED7018ABDB6A084FE9B41F40119D390BA565940816A18279F7D33`
- `pc-upgrade.glb`: `4FED36F137D0D17AC6E6D5077D01D8357AFC1189A7A9640C1891EEC2B00A9F24`
- Preview: `3790DE822BE0B7EC3F371D0825EDCCB04F77D9D4875EBFA3E69290B7DF439961`

## Preview

- [Ảnh PC sau khi tinh chỉnh](../artifacts/pc-upgrade/pc-room-context-after.png)

## Khi xem trên website

Sau khi deploy build mới, nên dùng `Ctrl + F5` để tránh trình duyệt giữ cache của `pc-upgrade.glb` hoặc bundle JavaScript cũ.

