# Naming conventions

## File và folder

- Folder, JavaScript module, stylesheet và asset dùng `kebab-case`.
- Không dùng khoảng trắng, underscore hoặc chữ hoa trong tên file mới.
- Chọn tên mô tả đúng mục đích; tránh các hậu tố mơ hồ như `final`, `new`, `test2` hoặc `copy`.
- Khi đổi tên file đã được Git theo dõi, dùng `git mv` và cập nhật toàn bộ import, URL, loader và reference liên quan.
- `README.md` và `LICENSE.md` giữ tên tài liệu chuẩn. Các file decoder Draco giữ tên upstream vì `DRACOLoader` phụ thuộc vào chúng.

## JavaScript

- Variable và function dùng `camelCase`.
- Class và constructor dùng `PascalCase`.
- Constant dùng chung dùng `UPPER_SNAKE_CASE`.
- Boolean bắt đầu bằng `is`, `has`, `can` hoặc `should`.
- Tránh tên viết tắt khó hiểu.
- Story data đặt trong `src/data/stories.js`; logic modal đặt trong `src/components/story-modal.js`.

## HTML và CSS

- CSS class và HTML id dùng `kebab-case` và tên theo component.
- Tránh selector phụ thuộc quá sâu vào cấu trúc HTML.
- Cleanup naming không được làm thay đổi thiết kế hiện có.

## Blender và Three.js

- Không đổi mesh/object name sang `kebab-case` khi code dùng token để nhận diện interaction.
- Giữ dạng `Story_<Key>_<Object>_Hover_Raycaster_Pointer` và giữ nguyên các token `Story`, `Hover`, `Raycaster`, `Pointer`.
- Không đổi tên hoặc di chuyển cây Blender nếu chưa xác minh texture và external link vẫn hoạt động.
