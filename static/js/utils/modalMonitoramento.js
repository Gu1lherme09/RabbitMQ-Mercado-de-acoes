document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('monitoramentoModal');
  const form = document.getElementById('formMonitoramento');
  const cancelar = document.getElementById('btnCancelar');


  // Abrir modal
  document.querySelectorAll('.btn-add').forEach(btn => {
    btn.addEventListener('click', () => {
      const acaoId = btn.dataset.acaoId;
      const simbolo = btn.dataset.simbolo;
      const nome = btn.dataset.nome;

      document.getElementById('modal_acao_id').value = acaoId;
      document.getElementById('modal_acao_simbolo').textContent = simbolo;
      document.getElementById('modal_acao_nome').textContent = nome;

      modal.classList.remove('hidden');
    });
  });

  // Fechar modal
  cancelar.addEventListener('click', () => {
    modal.classList.add('hidden');
  });

  // Enviar via AJAX 
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(form);
    const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;

    try {
      const response = await fetch(form.action, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken },
        body: formData
      });

      if (response.ok) {
        // ✅ Guarda a mensagem pra usar DEPOIS do reload
        sessionStorage.setItem('monitoramento_sucesso_msg', '✅ Monitoramento salvo com sucesso!');
        sessionStorage.setItem('monitoramento_sucesso_tipo', 'success');

        modal.classList.add('hidden');
        form.reset();

        // 🔹 Só recarrega aqui
        window.location.reload();
      }
      else {
        // Aqui sim pode mostrar direto (sem reload)
        showToast('⚠️ Erro ao salvar o monitoramento.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('❌ Erro na requisição.', 'error');
    }
  });
});
