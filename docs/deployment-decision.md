# Quyết định deploy portfolio

Ngày đánh giá: 2026-09-03

## Kết luận

**Nên deploy ngay một bản v1/soft launch lên domain mới, sau đó tiếp tục chỉnh sửa trên môi trường development hoặc staging.**

Không cần đợi website “hoàn hảo” mới deploy. Bản production thật giúp kiểm tra sớm DNS, HTTPS, cache, tốc độ tải model/texture, thiết bị di động và các hành vi tương tác mà localhost khó phản ánh đầy đủ.

Chưa nên quảng bá rộng ngay ngày đầu. Hãy coi lần deploy này là bản kiểm thử trên domain thật; khi checklist bên dưới đạt thì mới công bố portfolio.

## Trạng thái hiện tại

- Git working tree sạch trước lần kiểm tra build.
- `npm run build` hoàn tất thành công bằng Vite `6.4.3`.
- Website đang tải đúng:
  - `/models/room-main.glb`
  - `/models/outside-tree.glb`
  - `/models/facebook-card.glb`
  - Tám Grounded Pastel Day/Night texture atlas.
- `My Room - FINAL.blend` là file Blender authoring/final để lưu trữ; website không tải trực tiếp file `.blend` này.
- Chưa thấy file cấu hình riêng cho Vercel, Netlify, Firebase hoặc Cloudflare trong repository.

## Kết quả production build

| Thành phần | Kích thước | Gzip |
| --- | ---: | ---: |
| `index.html` | 32.29 kB | 8.35 kB |
| CSS | 27.32 kB | 6.13 kB |
| JavaScript | 825.83 kB | 215.31 kB |

Build có hai cảnh báo nhưng chưa chặn soft launch:

1. `src/main.js` có sử dụng `eval` gần dòng 1930. Nên thay sau vì không tốt cho bảo mật và tối ưu minify.
2. JavaScript chunk lớn hơn 500 kB. Có thể tối ưu sau bằng code splitting/dynamic import; cần ưu tiên nếu đo thấy tải chậm trên mạng di động.

## Workflow đề xuất

1. Chốt commit/tag hiện tại làm mốc `v1`.
2. Deploy production build lên hosting và kết nối domain.
3. Bật HTTPS và kiểm tra cả domain gốc lẫn `www`; chọn một địa chỉ canonical và redirect địa chỉ còn lại.
4. Không quảng bá rộng trong 24–48 giờ đầu.
5. Test trên điện thoại thật và máy tính:
   - tải room thành công;
   - Day/Night chuyển đúng;
   - cây hiển thị và shading đúng;
   - Facebook hover/click đúng;
   - GitHub/YouTube và các nút điều hướng đúng;
   - âm thanh chỉ chạy sau tương tác người dùng;
   - refresh trực tiếp trên domain không trả về 404;
   - không có lỗi nghiêm trọng trong Console/Network.
6. Tiếp tục chỉnh sửa trên branch hoặc staging preview, rồi merge/deploy khi từng thay đổi đã được kiểm tra.

## Mốc quyết định

- **Deploy bây giờ:** Có.
- **Công bố rộng ngay:** Chưa; đợi kiểm thử domain thật.
- **Tiếp tục chỉnh sửa:** Có, nhưng thực hiện sau trên development/staging thay vì thay trực tiếp bản production.
- **Cần sửa cảnh báo bundle trước khi deploy:** Không bắt buộc cho soft launch; nên đưa vào vòng tối ưu tiếp theo.
