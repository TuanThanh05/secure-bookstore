"use strict";

// Nút đóng thông báo
document.addEventListener("click", function (event) {
  const button = event.target.closest(".messages__close");
  if (!button) return;
  const item = button.closest(".messages__item");
  if (item) item.classList.add("is-hidden");
});

function getCsrfToken() {
  const input = document.querySelector("input[name=csrfmiddlewaretoken]");
  return input ? input.value : "";
}

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
