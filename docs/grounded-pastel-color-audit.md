# Báo cáo kiểm tra và kế hoạch đổi màu Grounded Pastel

Bạn nói đúng: cách phủ màu bằng shader là sai workflow của dự án này. Căn phòng phải đổi material trong Blender rồi bake lại texture; shader chỉ nên trộn Day/Night.

Sau khi đọc yêu cầu đính kèm, quá trình triển khai đã được dừng lại để kiểm tra và xác nhận đúng pipeline trước.

## Pipeline màu gốc

```text
Before Baking.blend
  → material gốc + ánh sáng ban ngày
  → bake 4 atlas 4096px

For Night Time Baking.blend
  → cùng palette + ánh sáng ban đêm
  → bake 4 atlas 4096px

For Export.blend
  → mesh đã UV theo First / Second / Third / Fourth

8 texture WebP
  → textureMap trong main.js
  → theme shader trộn Day/Night bằng uMixRatio
```

Đây cũng là cấu trúc của [repository gốc](https://github.com/andrewwoan/sooahs-room-folio/tree/main/blender%20files). `main.js` gốc chỉ nạp bốn cặp texture và tạo `roomMaterials`; màu phòng không được tạo bằng cách tô từng mesh trong Three.js. [Xem pipeline gốc](https://raw.githubusercontent.com/andrewwoan/sooahs-room-folio/main/src/main.js).

## 1. Màu nào đến từ Blender và texture bake?

Hầu hết vật thể đặc trong căn phòng lấy màu từ tám atlas Day/Night:

- `First`: vỏ phòng, tường/sàn, đá, clock và một phần gỗ.
- `Second`: backdrop, poster và photo frame.
- `Third`: piano, microphone, cây/đá ngoài phòng và một số decoration.
- `Fourth`: bàn ghế, computer, drawer, keyboard, sách, đèn và phần lớn đồ trang trí.

Trong `blender files/Before Baking.blend`, các material hồng/tím lớn gồm:

- `Room`
- `Chair Cushion`
- `Computer`
- `Drawer`
- `Drawer Shelves`
- `Desk Pad`
- `Keyboard`
- `Stone wall`
- `Base Purple`
- `Welcome Mat`

Các material cần giữ:

- `Wood`, `Light Wooden`: gỗ tự nhiên.
- Material sách, poster, đồ chơi và hoa: vẫn đa màu.
- `Plant Gradient`, `Hanging Plant`, `Plant Stem`: chỉ chỉnh nhẹ về sage.

Các ngoại lệ không hoàn toàn phụ thuộc atlas:

- Glass, water, bubble và video screen được gán material riêng trong JavaScript.
- Facebook là model/material riêng.
- Cây ngoài cửa sổ sử dụng shader riêng.

## 2. Màu nào đến từ SCSS?

Hệ thống UI nằm ở:

- `src/style.scss`
- `src/styles/variables.scss`

`$themes` điều khiển màu light/dark cho button, modal, icon, border và control. Repository gốc cũng dùng chính cấu trúc map này. [Xem SCSS gốc](https://github.com/andrewwoan/sooahs-room-folio/blob/main/src/style.scss).

Ngoài theme map, SCSS hiện còn màu hardcode cho:

- Welcome screen.
- Loading screen.
- Modal/story.
- Nút Skip room.
- Night-mode glow.
- Ambient background.

Những phần này không cần bake Blender.

## 3. Màu nào hardcode trong JavaScript?

Trong `src/main.js`:

- `scene.background`
- Border/background/text của loading button
- Nền loading screen sau khi Enter
- Water, glass và bubble
- Màu Facebook
- Tint ánh sáng của cây

Scene và loading sẽ đổi sang Mist Gray/Warm Cream/Deep Sage. Water, Facebook và các màu nhận diện tự nhiên sẽ không bị ép thành sage.

## 4. Những file cần thay đổi

- Tạo bản làm việc từ `blender files/Before Baking.blend`.
- Đồng bộ palette sang `blender files/For Night Time Baking.blend`.
- Dùng `blender files/For Export.blend` để kiểm tra atlas/UV, không sửa object name.
- Bake lại 8 texture trong `public/textures/room/day` và `public/textures/room/night`.
- Cập nhật `src/style.scss`.
- Cập nhật `src/styles/variables.scss`.
- Cập nhật một số màu hardcode trong `src/main.js`.
- Khôi phục `src/shaders/theme/fragment.glsl` về shader gốc chỉ dùng `uMixRatio`.

Không cần xuất lại `room-main.glb` nếu geometry, UV và object name không đổi.

Lưu ý: upstream dùng tên có dấu gạch dưới, nhưng fork hiện tại đang chạy tên có dấu gạch ngang như `first-texture-set-day.webp`. Cần giữ tên hiện tại để `textureMap` không bị hỏng.

## 5. Phần nào cần rebake?

| Phần | Cần rebake? |
|---|---|
| Tường, sàn, furniture và props trong phòng | Có |
| Day palette | Có, bốn atlas |
| Night palette | Có, bốn atlas |
| Gỗ tự nhiên | Không đổi material, nhưng vẫn xuất hiện trong atlas bake mới |
| SCSS/UI | Không |
| Scene background/loading | Không |
| Facebook | Không |
| Cây ngoài cửa sổ | Không thuộc room atlas |
| Shader Day/Night | Không; chỉ khôi phục kiến trúc gốc |
| GLB | Không, nếu UV/geometry không đổi |

## Kế hoạch triển khai

1. Khôi phục hoàn toàn shader gốc, loại bỏ mọi recolor toàn cảnh và uniform màu tạm.
2. Sao lưu tám atlas hiện tại. Ba atlas trong dự án đã khác bản trong thư mục Blender, nên không được ghi đè thiếu kiểm soát.
3. Tạo bản Blender Grounded Pastel từ `Before Baking.blend`.
4. Đổi shared material theo tỷ lệ 60/25/10/5:
   - Room → Warm Cream/Mist Gray.
   - Furniture lớn → Sage/Dusty Blue/cream.
   - Wood giữ nguyên.
   - Props nhỏ giữ terracotta, vàng, xanh, dusty rose.
5. Áp cùng nhận diện palette cho file Night với charcoal sage, dark blue, warm brown và dim cream.
6. Bake lại First–Fourth cho cả Day và Night, giữ nguyên UV và độ phân giải 4096px.
7. Chép hoặc convert kết quả sang tám đường dẫn WebP hiện tại.
8. Đổi SCSS sang Deep Sage/Sage/Warm Cream/Mist Gray.
9. Đổi scene/loading hardcode trong JavaScript.
10. Build và kiểm tra texture load, `uMixRatio`, theme toggle, hover/click và raycaster.

## Bảng màu mục tiêu

### Main / anchor

- Deep Sage: `#405D52`
- Sage Green: `#718E7A`

### Secondary

- Dusty Blue: `#8FA9B8`

### Warm accents

- Soft Terracotta: `#D99478`
- Muted Yellow: `#D8BA68`

### Neutral bases

- Warm Cream: `#F1E9DE`
- Mist Gray: `#DCE2DE`

### Optional accent

- Dusty Rose: `#D6A0A0`

## Phân cấp màu đề xuất

- 60% neutral: Warm Cream, Mist Gray và natural wood.
- 25% calm colors: Sage và Dusty Blue.
- 10% warm personality: Terracotta và peach.
- 5% playful accents: Muted Yellow, Dusty Pink, blue, green và các pastel nhỏ khác.

Nguyên tắc chính:

> Large surfaces = calm and grounded. Small objects = colorful and expressive.

## Trạng thái Blender và phương án bake

Các file Blender đang dùng Cycles và cấu hình bake `COMBINED`, margin 16px. File nguồn còn lưu cấu hình `SimpleBake` với atlas 4096px, nhưng add-on `SimpleBake` hiện chưa được cài hoặc bật trong Blender 5.2.

Phương án đề xuất là dùng Cycles bake tích hợp của Blender và các UV atlas hiện có. Cách này không cần tải add-on bên ngoài, vẫn giữ nguyên:

- UV mapping.
- First/Second/Third/Fourth texture sets.
- Day/Night texture architecture.
- Object names.
- GLB structure.
- Three.js `roomMaterials` và `uMixRatio`.

## Những phần phải giữ nguyên

- Camera behavior.
- Raycasting.
- Hover animations.
- Click interactions.
- Social links.
- Theme toggle.
- Sound toggle.
- Loading animation.
- Day/Night transition.
- Existing GLB object naming.
- Texture atlas architecture.
- Natural wood appearance.
- Màu sắc biểu cảm của các vật trang trí nhỏ.

