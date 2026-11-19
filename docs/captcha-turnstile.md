# CAPTCHA ở trang đăng ký – Cloudflare Turnstile

## 1. Để làm gì

Trang đăng ký bước 1 (nhập email) gửi thư ra ngoài, nên bot có thể lạm dụng để spam hộp thư người khác (*email bombing*). Giới hạn tần suất đã có (theo email và theo IP, xem `docs/dang-ky-tai-khoan.md` mục 4), nhưng bot dùng nhiều IP vẫn lách được giới hạn theo IP. Turnstile thêm một lớp nữa: trình duyệt phải giải một thử thách của Cloudflare (thường người dùng không phải làm gì, hoặc chỉ bấm một ô) thì mới gửi được form. Đây là phòng thủ nhiều lớp, **không thay** các giới hạn đã có.

Chỉ đặt ở bước 1. Không đặt ở bước bấm link (đã có link trong thư làm bằng chứng) và bước đặt tên đăng nhập, mật khẩu (đã có phiên chứng minh email).

## 2. Ngoại lệ luật "không CDN" (nhóm trưởng chốt 2026-11-19)

Turnstile bắt buộc tải `api.js` từ máy chủ Cloudflare và hiển thị trong một iframe, không tự host được. Vì vậy **chỉ riêng view `accounts:register`** dùng `@csp_override(settings.SIGNUP_CSP)`:

- `script-src 'self' https://challenges.cloudflare.com`
- `frame-src https://challenges.cloudflare.com`

Mọi trang khác vẫn CSP chặt như cũ (test `test_page_shows_widget_and_relaxes_csp_only_here` kiểm tra trang đăng nhập, kiểm tra hộp thư, hoàn tất đăng ký không có Cloudflare trong CSP). Dự án không tự viết dòng JS nào: dùng *implicit rendering*, chỉ một thẻ `<div class="cf-turnstile">`, script của Cloudflare tự chèn ô ẩn `cf-turnstile-response` vào form.

Đánh đổi đã chấp nhận: đăng ký cần mạng tới Cloudflare và cần bật JavaScript (có `<noscript>` báo cho người dùng).

## 3. Server xử lý thế nào (`backend/core/captcha.py`)

Thứ tự ở bước 1 (`accounts.views.register`):

1. Form hợp lệ (email đúng dạng). Sai thì báo lỗi, không gọi Cloudflare.
2. Giới hạn theo IP (có sẵn). Vượt thì 429, **không gọi Cloudflare** – kẻ spam không biến được server thành công cụ gọi Cloudflare hàng loạt.
3. `verify_captcha(request, "signup")`:
   - Không có token hoặc token dài quá 2048 ký tự → từ chối ngay, không gọi Cloudflare.
   - POST tới `https://challenges.cloudflare.com/turnstile/v0/siteverify` bằng `urllib.request` có sẵn trong Python (không thêm thư viện), gửi `secret`, `response` (token), `remoteip` (IP người dùng), timeout 5 giây, đọc tối đa 64 KB.
   - Chỉ chấp nhận khi `success` đúng là `true`, `hostname` trùng tên miền đang truy cập, `action` đúng là `signup` (khớp `data-action` của widget). Với secret key thử của Cloudflare thì bỏ qua kiểm tra hostname và action (key thử nhận mọi token thử, chỉ dùng trên máy dev).
   - Cloudflare lỗi, quá thời gian hoặc trả dữ liệu lạ → **từ chối, không gửi thư** (không bao giờ bỏ qua CAPTCHA). Người dùng thấy "Hệ thống xác minh đang gặp sự cố" (503).
   - Token bị từ chối, giả, hết hạn, đã dùng (`timeout-or-duplicate`) → "Chưa xác minh được bạn không phải robot" (400).
4. Giới hạn theo email và gửi thư (có sẵn, không đổi).

Mỗi lần không đạt ghi log `captcha_failed` (cảnh báo) với `detail.reason` (`missing`, `invalid`, `rejected`, `hostname_mismatch`, `action_mismatch`, `unavailable`) và `detail.codes` (mã lỗi của Cloudflare, đã lọc chỉ giữ chữ thường, số, dấu gạch). **Log không bao giờ chứa token hay secret key.** CSRF của Django vẫn giữ nguyên (form vẫn có `csrfmiddlewaretoken`).

Chống dùng lại token do Cloudflare lo: mỗi token chỉ xác minh được một lần và hết hạn sau 5 phút.

**Chia sẻ dữ liệu với bên thứ ba:** server gửi IP người dùng (`remoteip`) cho Cloudflare để đánh giá chính xác hơn; trình duyệt người dùng cũng kết nối thẳng tới Cloudflare khi tải widget. Cần nêu trong báo cáo.

## 4. Cấu hình

`.env` (web đọc file này):

```
TURNSTILE_SITE_KEY=
TURNSTILE_SECRET_KEY=
```

- Để trống cả hai: Turnstile **tắt**, đăng ký chạy như trước (máy dev, CI). `runserver` báo cảnh báo `core.W001`.
- Key thử: cảnh báo `core.W002`.
- `bookstore.settings.prod` **không chạy** nếu thiếu key hoặc dùng secret key thử.
- Secret key là bí mật như mật khẩu: không commit, không chụp màn hình, không gửi cho ai.

**Key thử chính thức của Cloudflare** (công khai, chỉ để thử, dùng được trên `localhost`, token thử luôn là `XXXX.DUMMY.TOKEN.XXXX`):

| Mục đích | `TURNSTILE_SITE_KEY` | `TURNSTILE_SECRET_KEY` |
| --- | --- | --- |
| Luôn qua | `1x00000000000000000000AA` | `1x0000000000000000000000000000000AA` |
| Luôn bị chặn | `2x00000000000000000000AB` | `2x0000000000000000000000000000000AA` |
| Token đã dùng | `1x00000000000000000000AA` | `3x0000000000000000000000000000000AA` |
| Bắt giải thử thách | `3x00000000000000000000FF` | `1x0000000000000000000000000000000AA` |

Nếu Cloudflare đổi bộ key thử, xem trang "Testing" trong tài liệu Turnstile của Cloudflare.

## 5. Hướng dẫn test thật (từng bước)

Đổi `.env` xong phải **tắt `runserver` (Ctrl + C) rồi chạy lại** thì key mới có hiệu lực, và mở trang bằng **Ctrl + Shift + R**.

### Mức 1 – key thử, không cần tài khoản Cloudflare

1. Điền dòng "Luôn qua" ở bảng trên vào `.env`, chạy `python manage.py runserver`.
2. Mở `http://127.0.0.1:8000/account/register/`: dưới ô email có ô Turnstile ghi đây là bản thử.
3. Nhập email, bấm "Gửi link đăng ký" → sang trang "Kiểm tra hộp thư", thư có link (in ra terminal nếu chưa cấu hình Gmail).
4. Đổi sang dòng "Luôn bị chặn", chạy lại, gửi form → báo "Chưa xác minh được bạn không phải robot", không có thư.
5. Đổi sang dòng "Token đã dùng", chạy lại, gửi form → cũng bị chặn; vào Dashboard → Nhật ký → lọc "CAPTCHA không đạt" thấy `codes: ["timeout-or-duplicate"]`.

### Mức 2 – widget thật (dùng khi demo)

1. Vào `dash.cloudflare.com`, đăng nhập, chọn **Turnstile** ở menu trái (có thể nằm trong mục "Application security" hoặc gõ "Turnstile" vào ô tìm kiếm).
2. Bấm **Add widget**:
   - **Widget name:** `secure-bookstore`.
   - **Hostname:** thêm `localhost` (khi demo trên máy) và tên miền thật nếu có. Mở web bằng `127.0.0.1` thì thêm cả `127.0.0.1`, hoặc mở bằng `http://localhost:8000` cho khớp.
   - **Widget Mode:** **Managed**.
   - Câu hỏi "pre-clearance": chọn **No**.
3. Bấm **Create**: Cloudflare hiện **Site Key** và **Secret Key**. Chép vào `.env` (`TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY`). Không dán secret key vào chat, ảnh chụp hay commit.
4. Chạy lại `runserver`, mở trang đăng ký bằng đúng tên miền đã khai báo. Ô xác minh thật hiện ra; đăng ký như người dùng bình thường.
5. Mục **Analytics** của widget trên Cloudflare Dashboard thấy số lượt thử thách và số lượt xác minh.

Lỗi hay gặp: ô báo "domain not allowed" (mã 110200) → hostname đang mở chưa có trong danh sách của widget; log `hostname_mismatch` → mở web bằng tên miền khác với tên Cloudflare trả về.

### Mức 3 – thử tấn công (quay video demo)

Chạy với key thật (mức 2). Mỗi lệnh một khối, chạy ở bất kỳ thư mục nào.

**a) Bot gửi form không giải CAPTCHA:**

```zsh
curl -s -c /tmp/jar -b /tmp/jar http://localhost:8000/account/register/ -o /tmp/reg.html
```

```zsh
CSRF=$(grep -o 'name="csrfmiddlewaretoken" value="[^"]*"' /tmp/reg.html | sed 's/.*value="//;s/"$//')
```

```zsh
curl -s -o /dev/null -w "%{http_code}\n" -b /tmp/jar -c /tmp/jar --data-urlencode "csrfmiddlewaretoken=$CSRF" --data-urlencode "email=bot@example.com" http://localhost:8000/account/register/
```

Kết quả `400`, không có thư, Nhật ký có `captcha_failed` lý do `missing`.

**b) Dùng lại token đã dùng (replay):**

1. Mở trang đăng ký bằng trình duyệt, bấm F12 → tab **Network**, đăng ký thật một lần.
2. Bấm vào request `register/` (POST) → tab **Payload** → chép giá trị `cf-turnstile-response`.
3. Chạy lại 2 lệnh đầu ở mục a) để có CSRF mới, rồi (thay `<TOKEN>` bằng giá trị vừa chép):

```zsh
curl -s -o /dev/null -w "%{http_code}\n" -b /tmp/jar -c /tmp/jar --data-urlencode "csrfmiddlewaretoken=$CSRF" --data-urlencode "email=bot2@example.com" --data-urlencode "cf-turnstile-response=<TOKEN>" http://localhost:8000/account/register/
```

Kết quả `400`, Nhật ký có `captcha_failed` lý do `rejected`, `codes: ["timeout-or-duplicate"]`.

**c) Giả token:** như b) nhưng `<TOKEN>` là chuỗi tự bịa → `400`, `codes: ["invalid-input-response"]`.

Mỗi IP chỉ gửi bước 1 được 5 lần trong 10 phút: thử nhiều quá sẽ nhận `429` (đó là giới hạn tần suất đang làm việc, đợi 10 phút hoặc khởi động lại `runserver`).

## 6. Kiểm thử tự động

- `core/tests/test_captcha.py` (19 test): Siteverify giả (mock `urlopen`), token hợp lệ, thiếu, quá dài, giả, hết hạn/dùng lại, `success` không đúng `true`, sai hostname, hostname có cổng, sai action, timeout/mất kết nối, phản hồi rác, mã lỗi lạ bị lọc, log không chứa token/secret, key thử, Turnstile tắt, cảnh báo `core.W001`/`core.W002`.
- `accounts/tests/test_signup_captcha.py` (11 test): trang có widget và CSP chỉ nới ở trang này, thiếu token/token sai/sai hostname-action/Cloudflare lỗi đều không gửi thư, vượt giới hạn IP thì không gọi Cloudflare, CAPTCHA đạt nhưng email vượt giới hạn giờ thì vẫn không gửi thư, email sai không gọi Cloudflare, CSRF vẫn bắt buộc, Turnstile tắt thì không có widget.
- CI không gọi Cloudflare thật và không dùng key thật nào (bước `check --deploy` dùng chuỗi giả chỉ để settings prod chạy được).

**Chưa kiểm chứng được trong môi trường của Claude:** widget thật trên trình duyệt và lời gọi Siteverify thật (môi trường không ra được Internet tới Cloudflare). Đã thử thật phần còn lại trên MySQL: trang đăng ký trả đúng CSP, có thẻ widget; gửi form không có token → 400 + log; có token nhưng không tới được Cloudflare → 503, không gửi thư. Nhóm trưởng tự kiểm chứng phần widget bằng mục 5.
