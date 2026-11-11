/* =====================================================================
   base.js – JavaScript CHUNG (nhóm trưởng giữ). Nạp ở cuối base.html với defer.
   Quy tắc (CSP + chống DOM XSS):
     - Không viết JS inline trong HTML, không dùng onclick="...".
     - Gắn sự kiện bằng addEventListener.
     - Hiển thị dữ liệu bằng textContent, KHÔNG dùng innerHTML.
     - AJAX gửi CSRF token qua header X-CSRFToken, lấy từ {% csrf_token %} trong trang.
   ===================================================================== */
"use strict";

// Nút đóng thông báo
document.addEventListener("click", function (event) {
  const button = event.target.closest(".messages__close");
  if (!button) return;
  const item = button.closest(".messages__item");
  if (item) item.classList.add("is-hidden");
});

/**
 * Lấy CSRF token từ ô ẩn mà {% csrf_token %} sinh ra trong trang.
 * (Cookie CSRF đặt HttpOnly nên JS không đọc cookie.)
 */
function getCsrfToken() {
  const input = document.querySelector("input[name=csrfmiddlewaretoken]");
  return input ? input.value : "";
}

/**
 * Gửi POST bằng fetch, kèm CSRF token. Trả về JSON.
 * Dùng chung cho các AJAX nhỏ (cập nhật giỏ hàng...).
 */
async function postForm(url, data) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "X-CSRFToken": getCsrfToken() },
    body: new URLSearchParams(data),
    credentials: "same-origin",
  });
  if (!response.ok) {
    throw new Error("Yêu cầu thất bại: " + response.status);
  }
  return response.json();
}

window.Bookstore = { getCsrfToken, postForm };
