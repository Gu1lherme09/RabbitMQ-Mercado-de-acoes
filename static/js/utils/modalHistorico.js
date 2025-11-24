document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('monitoramentoModal');
  const cancelar = document.getElementById('btnCancelar');
  const salvar = document.getElementById('btnSalvarHistorico');
  const selectPeriodo = document.getElementById('selectPeriodo');
  const resultado = document.getElementById('resultadoHistorico');
  const periodoSelectEl = document.getElementById('selectPeriodo');

  let simboloAtual = null;


  document.querySelectorAll('.btn-add').forEach(btn => {
    btn.addEventListener('click', () => {
      simboloAtual = btn.dataset.simbolo;
      const nome = btn.dataset.nome;

      document.getElementById('modal_acao_simbolo').textContent = simboloAtual;
      document.getElementById('modal_acao_nome').textContent = nome;

      resultado.textContent = "";
      modal.classList.remove('hidden');
    });
  });

  salvar.addEventListener('click', async () => {
    if (!simboloAtual) return;
    const periodo = selectPeriodo.value;
    
    resultado.innerHTML = "⏳ Buscando e salvando histórico...";

    try {
      const resp = await fetch(`/api/historico/${simboloAtual}/?periodo=${periodo}`);
      const data = await resp.json();

      if (data.ok) {
        resultado.innerHTML = `✅ ${data.msg}`;
      } else {
        resultado.innerHTML = `⚠️ ${data.erro || "Erro ao salvar histórico."}`;
      }
    } catch (err) {
      console.error(err);
      resultado.innerHTML = "❌ Erro de conexão com o servidor.";
    }
  });

  cancelar.addEventListener('click', () => {
    modal.classList.add('hidden');
  });
});
