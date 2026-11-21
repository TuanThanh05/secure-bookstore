"use strict";

document.querySelectorAll("[data-copy-target]").forEach(function (button) {
  const source = document.getElementById(button.getAttribute("data-copy-target"));
  const status = document.querySelector("[data-copy-status]");
  if (!source || !navigator.clipboard || !window.isSecureContext) return;

  button.hidden = false;
  button.addEventListener("click", function () {
    navigator.clipboard.writeText(source.textContent.trim()).then(function () {
      if (status) status.textContent = "Đã sao chép 5 mã dự phòng.";
    }, function () {
      if (status) status.textContent = "Không sao chép được. Hãy chép tay hoặc bấm Tải xuống.";
    });
  });
});
