# PC blush–lavender material correction

Ngày hoàn tất: 2026-09-04

Trạng thái: **Hoàn tất và đã xác minh**

## Nguyên nhân màu bị loang và nhấp nháy

PC xanh cũ nằm trong mesh atlas gộp `Fourth`, trong khi `pc-upgrade.glb` đặt một PC mới đúng cùng vị trí. Code trước đã cố loại PC cũ bằng bounding box lấy từ Blender, nhưng Blender dùng hệ trục Z-up còn GLTFLoader/Three.js dùng Y-up.

Do bounding box dùng sai hệ trục, PC cũ thực tế không bị loại trên website. Hai bề mặt nằm gần như trùng nhau gây **z-fighting**, tạo vệt xanh loang và nhấp nháy liên tục.

Tọa độ đã được sửa theo phép đổi:

```text
Blender (X, Y, Z) → Three.js (X, Z, -Y)
```

Bounding box PC trên web hiện là:

```text
min = (-3.27, 3.07, -4.00)
max = (-1.25, 4.60, -3.145)
```

## Bản sửa hiện tại

- Loại đúng các tam giác PC cũ khỏi `Fourth` tại runtime.
- Ẩn các helper cũ `Computer_Fan_*` và `Computer_Glass`.
- Chỉ render một case hoàn chỉnh từ `pc-upgrade.glb`; không còn hai bề mặt case chồng nhau.
- Xóa `31` polygon thừa tạo thành `62` tam giác trùng khít trong chính case; hình dáng nhìn thấy không đổi.
- Đặt ambient lavender glow vào đúng hệ tọa độ Three.js: `(-2.2, 3.84, -3.38)`.
- Thêm cache-busting `?v=20260904-clean` vào URL model để trình duyệt/CDN không dùng lại GLB cũ còn mặt trùng.
- Giảm highlight trắng của case để bề mặt không bị cháy sáng.
- Khôi phục hướng màu blush–mauve–lavender theo hình tham chiếu thứ hai.
- Giữ nguyên hình dáng, kích thước, vị trí PC, camera, bố cục phòng và các đồ vật khác.
- Không ghi đè room atlas và không sửa `room-main.glb`.

## Màu đã chốt

### Blender

| Thành phần | Màu | Hex |
| --- | --- | --- |
| Vỏ chính | Blush White | `#EADDE3` |
| Viền/vỏ phụ | Lavender Mist | `#D8C7DD` |
| Kính | Cool Lavender Glass | `#D9CBE5` |
| Nội thất trung tính | Mauve Gray | `#8F8193` |
| GPU | Muted Plum | `#74617F` |
| Motherboard | Mauve | `#A582A4` |
| Chi tiết nhỏ | Soft Lavender | `#BBA8CC` |
| Fan accents | Pastel Lilac | `#CBB3DB` |
| LED | Pastel Lavender | `#D8B5EE` |

### Web

Shader web cần màu nền đậm hơn một chút để sau tone mapping cho kết quả gần hình tham chiếu:

| Thành phần | Day | Night |
| --- | --- | --- |
| Vỏ chính | `#CDBBC5` | `#756770` |
| Viền/vỏ phụ | `#B9A8C3` | `#695C72` |
| Kính | `#CBB9D5` | Theo ánh sáng môi trường |

Thông số kính web: transmission `0.72`, opacity `0.22`, roughness `0.12`. Ambient glow dùng opacity `0.32`; đèn lavender trong file Blender dùng energy `55`.

## Xác minh chống nhấp nháy

Vùng lọc mới được kiểm tra trong đúng hệ tọa độ web:

- Tổng tam giác của `Fourth`: `64,248`.
- Tam giác trong vùng PC cũ được loại: `5,236`.
- Tam giác còn lại: `59,012`.
- Tỷ lệ vùng thay thế: `8.1497%`.

Kết quả này xác nhận bounding box mới đã chạm đúng PC; bounding box cũ nằm sai phía trên trục Z của Three.js.

Kiểm tra riêng case sau khi dọn mặt trùng:

- Tam giác trước khi dọn: `4,946`.
- Tam giác sau khi dọn: `4,884`.
- Tam giác trùng khít còn lại: `0`.

## File đã cập nhật

- [My Room - FINAL.blend](../blender%20files/My%20Room%20-%20FINAL.blend)
- [pc-upgrade.glb](../public/models/pc-upgrade.glb)
- [src/main.js](../src/main.js)
- [PC fragment shader](../src/shaders/pc/fragment.glsl)
- [upgrade_pc_area.py](../scripts/blender/upgrade_pc_area.py)
- [audit_room_pc_removal.py](../scripts/blender/audit_room_pc_removal.py)
- [audit_pc_duplicate_faces.py](../scripts/blender/audit_pc_duplicate_faces.py)
- [verify_final_room_blend.py](../scripts/blender/verify_final_room_blend.py)

## Kết quả kiểm thử

- Blender verification: **Pass**.
- Final Blender: `184` objects, `181` meshes, `161` baked room meshes.
- Case giữ nguyên `2,904` vertices; polygon giảm từ `2,439` xuống `2,408` do loại đúng `31` mặt trùng khít, không làm đổi silhouette.
- Missing external images: `0`.
- `pc-upgrade.glb`: `17` meshes, `9` materials, `88,196` bytes.
- `npm run build`: **Pass**, Vite `6.4.3`.
- Production bundle: `dist/assets/index-BvNas232.js`.
- Trang chính, source JavaScript, PC GLB và PC shader đều trả HTTP `200`.

SHA-256:

- `My Room - FINAL.blend`: `15C102DC317FF9B663C234B6D4947F06F4F9C058515FAC815F6736612B8825C2`
- `pc-upgrade.glb`: `DBD6444398A892DB2A87D211FCAC3BE42645134128BC9A5F2581736DE0CF7937`
- Preview: `504F603D990C561C9F11B0EE3A7AB0BBBD8A643AF79781399DF1BC106ACD03AB`

## Preview

- [Ảnh PC Blender sau khi sửa](../artifacts/pc-upgrade/pc-room-context-after.png)

## Lưu ý khi xem bản deploy

Cần deploy lại cả bundle và `pc-upgrade.glb`. URL model mới đã có revision để né cache cũ; vẫn nên dùng `Ctrl + F5` sau khi deploy.
