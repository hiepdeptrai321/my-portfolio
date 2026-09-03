# PC pink–purple correction

Ngày cập nhật: 2026-09-03  
Trạng thái: **Đã thay thế bản PC quá trắng bằng palette hồng tím theo ảnh tham chiếu**

## Nội dung đã sửa

- Vỏ trắng lạnh `#F1EEE8` được thay bằng Blush White `#EADDE3`.
- Trim xanh–xám được thay bằng Lavender Mist `#D8C7DD`.
- Motherboard Sage được thay bằng Mauve `#A582A4`.
- GPU Deep Sage được thay bằng Muted Plum `#74617F`.
- Internal accents chuyển sang Soft Lavender `#BBA8CC` và Pastel Lilac `#CBB3DB`.
- Kính dùng lavender tint `#D9CBE5`.
- LED chuyển sang lavender hồng `#D8B5EE`.
- Thêm vòng sáng quạt ở góc trên trái theo ảnh tham chiếu.
- Giữ ba quạt GPU phía dưới, trong đó quạt giữa có glow nhẹ.
- Tăng ánh tím nội thất và thêm radial ambient glow trên web.

## Những phần được giữ nguyên

- Kích thước, vị trí và hình dáng PC.
- Camera và bố cục căn phòng.
- UV và `2,904` vertices / `2,439` polygons của case gốc.
- Tám room texture atlases.
- Các đồ trang trí ngoài khu vực PC.
- Animation quạt hiện có và chuyển theme Day/Night.

## Xác minh

- Blender verification: **Pass**.
- `npm run build`: **Pass**.
- Final Blender SHA-256: `0638C08AD9E306F509FDB98B8FC1AF77EE24CF5BA05C822F95F8129A9B2B55FF`.
- PC GLB: `69,684` bytes, SHA-256 `2999BAD3A90ECA006B72289B7BD569746ED33FDEA197955085852F43B5802BBC`.
- Production JS: `dist/assets/index-DIhkyJj9.js`.

## Preview

- [PC hồng tím sau khi sửa](../artifacts/pc-upgrade/pc-room-context-after.png)
- [PC trước lần nâng cấp đầu tiên](../artifacts/pc-upgrade/pc-room-context-before.png)

## File chính

- [`My Room - FINAL.blend`](../blender%20files/My%20Room%20-%20FINAL.blend)
- [`pc-upgrade.glb`](../public/models/pc-upgrade.glb)
- [`src/main.js`](../src/main.js)
- [`upgrade_pc_area.py`](../scripts/blender/upgrade_pc_area.py)
