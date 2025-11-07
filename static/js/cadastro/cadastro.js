document.addEventListener("click", (e) => {
    const btn = e.target.closest(".toggle-password");
    if (!btn) return;

    const input = document.getElementById(btn.dataset.target);
    if (!input) return;

    const eyeOpen = btn.querySelector(".eye-open");
    const eyeClosed = btn.querySelector(".eye-closed");

    if (input.type === "password") {
        input.type = "text";
        eyeOpen.style.display = "inline-block";
        eyeClosed.style.display = "none";
    } else {
        input.type = "password";
        eyeOpen.style.display = "none";
        eyeClosed.style.display = "inline-block";
    }
});
