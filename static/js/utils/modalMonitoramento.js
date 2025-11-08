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
    e.preventDefault(); // ainda evita o reload automático

    const formData = new FormData(form);
    const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;

    try {
      const response = await fetch(form.action, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken
        },
        body: formData
      });

      if (response.ok) {
        alert('✅ Monitoramento salvo com sucesso!');
        modal.classList.add('hidden');
        form.reset();

        // 🔹 recarrega a página para mostrar a nova ação
        window.location.reload();
      } else {
        alert('⚠️ Erro ao salvar o monitoramento.');
      }
    } catch (err) {
      console.error(err);
      alert('❌ Erro na requisição.');
    }
  });
});




