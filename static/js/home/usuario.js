
document.addEventListener("DOMContentLoaded", () => {
  const trigger = document.getElementById("user-trigger");
  const dropdown = document.getElementById("user-dropdown");
  const menu = document.getElementById("user-menu");

  if (!trigger || !dropdown || !menu) return;

  // abre/fecha o dropdown no clique
  trigger.addEventListener("click", (e) => {
    e.stopPropagation();
    dropdown.classList.toggle("show");
  });

  // fecha ao clicar fora
  document.addEventListener("click", (e) => {
    if (!menu.contains(e.target)) {
      dropdown.classList.remove("show");
    }
  });

  // fecha ao apertar ESC
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") dropdown.classList.remove("show");
  });
});

