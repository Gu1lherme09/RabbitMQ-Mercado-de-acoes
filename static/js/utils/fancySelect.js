document.addEventListener("DOMContentLoaded", () => {

  document.querySelectorAll("select[data-fancy]").forEach(selectEl => {

    // esconder select real
    selectEl.style.display = "none";

    // criar container
    const wrapper = document.createElement("div");
    wrapper.classList.add("custom-dropdown");
    wrapper.setAttribute("data-dropdown-select", selectEl.id);

    // botão do dropdown
    const btn = document.createElement("button");
    btn.type = "button";
    btn.classList.add("custom-dropdown-toggle");
    btn.innerHTML = `
      <span class="custom-dropdown-label"></span>
      <span class="custom-dropdown-icon">▾</span>
    `;

    // lista de opções
    const menu = document.createElement("ul");
    menu.classList.add("custom-dropdown-menu");

    // cria as opções
    [...selectEl.options].forEach(opt => {
      const li = document.createElement("li");
      li.textContent = opt.textContent;
      li.dataset.value = opt.value;

      if (opt.selected) li.classList.add("selected");

      menu.appendChild(li);

      li.addEventListener("click", () => {
        // marca visual
        menu.querySelectorAll("li").forEach(i => i.classList.remove("selected"));
        li.classList.add("selected");

        // atualiza o select REAL
        selectEl.value = opt.value;

        // dispara evento change
        selectEl.dispatchEvent(new Event("change"));

        // atualiza label
        label.textContent = opt.textContent;

        // fechar
        wrapper.classList.remove("open");
      });
    });

    // insert no DOM
    const label = btn.querySelector(".custom-dropdown-label");
    const selectedOpt = selectEl.options[selectEl.selectedIndex];
    label.textContent = selectedOpt.textContent;

    wrapper.appendChild(btn);
    wrapper.appendChild(menu);
    selectEl.insertAdjacentElement("afterend", wrapper);

    // evento abrir/fechar
    btn.addEventListener("click", e => {
      e.stopPropagation();
      const isOpen = wrapper.classList.contains("open");

      document.querySelectorAll(".custom-dropdown.open")
        .forEach(d => d.classList.remove("open"));

      if (!isOpen) wrapper.classList.add("open");
    });
  });

  // fechar ao clicar fora
  document.addEventListener("click", () => {
    document.querySelectorAll(".custom-dropdown.open")
      .forEach(d => d.classList.remove("open"));
  });
});
