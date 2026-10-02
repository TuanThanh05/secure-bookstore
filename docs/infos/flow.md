## Quy trình làm việc với Git

Mọi thành viên trong nhóm cần tuân thủ đúng luồng làm việc sau:

1. Trước khi bắt đầu làm việc, luôn lấy phiên bản mới nhất của dự án về máy.
2. Chuyển sang đúng branch được phân công trước khi code.
3. Tuyệt đối không code trực tiếp trên branch `main`.
4. Mỗi người chỉ làm trên branch được giao cho mình.
5. Khi hoàn thành phần việc, push code lên đúng branch đang làm.
6. Sau khi push, báo lại để kiểm tra và duyệt code.
7. Code chỉ được merge vào `secure-bookstore-dev` sau khi đã được duyệt.
8. Chỉ khi hoàn thành đầy đủ checkpoint và hệ thống đã được kiểm tra ổn định thì mới merge từ `secure-bookstore-dev` lên `main`.

Luồng tổng quát:

```text
Clone/Pull code mới nhất
        ↓
Chuyển sang branch được giao
        ↓
Code và kiểm thử
        ↓
Push lên đúng branch
        ↓
Báo để kiểm tra
        ↓
Merge vào secure-bookstore-dev
        ↓
Hoàn thành checkpoint
        ↓
Kiểm tra toàn bộ hệ thống
        ↓
Merge vào main