function showToast(message, type = "info", duration = 4000) {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.classList.add("toast", type);

  toast.innerHTML = `
    <span>${message}</span>
    <span class="toast-close">&times;</span>
  `;

  container.appendChild(toast);

  // força reflow pra ativar transição
  requestAnimationFrame(() => {
    toast.classList.add("toast-show");
  });

  // fechar no X
  toast.querySelector(".toast-close").addEventListener("click", () => {
    hideToast(toast);
  });

  // auto-hide
  if (duration > 0) {
    setTimeout(() => hideToast(toast), duration);
  }
}

function hideToast(toast) {
  toast.classList.remove("toast-show");
  setTimeout(() => {
    toast.remove();
  }, 250);
}
