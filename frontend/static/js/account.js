/* =====================================================================
   account.js – trang đăng nhập / đăng ký. Nạp bằng {% block extra_js %} (defer).
   Nút "con mắt" hiện/ẩn mật khẩu: chỉ đổi type của <input> (password ↔ text).
   Quy tắc CSP: không JS inline, gắn sự kiện bằng addEventListener, không innerHTML.
   ===================================================================== */
"use strict";

document.querySelectorAll(".password-toggle").forEach(function (button) {
  const input = document.getElementById(button.getAttribute("aria-controls"));
  if (!input) return;

  // Nút để sẵn thuộc tính hidden: trình duyệt tắt JS thì không thấy nút "chết"
  button.hidden = false;

  button.addEventListener("click", function () {
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    button.setAttribute("aria-pressed", String(show));
    button.setAttribute("aria-label", show ? "Ẩn mật khẩu" : "Hiện mật khẩu");
    input.focus();
  });

  // Gửi form thì luôn ẩn lại, để trình duyệt không lưu mật khẩu như một ô chữ thường
  if (input.form) {
    input.form.addEventListener("submit", function () {
      input.type = "password";
      button.setAttribute("aria-pressed", "false");
      button.setAttribute("aria-label", "Hiện mật khẩu");
    });
  }
});