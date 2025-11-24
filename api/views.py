import os , requests
from django.http import JsonResponse
from datetime import datetime
from typing import Optional, Dict
from django.conf import settings
from django.views.decorators.http import require_POST,require_GET


from monitoramento.services.publishers import publicar_tarefa_atualizar_acao, publicar_tarefa_atualizar_todas_acoes, publicar_tarefa_historico_acao
from tela_cadastro.models import Acao, AcaoHistorico

def safe_get(obj, key, default=0):
    """
    Retorna valor seguro de um dicionário, evitando None, KeyError e valores vazios.
    """
    if not obj:
        return default
    val = obj.get(key)
    return val if val not in (None, "", "null") else default

@require_POST
def atualizar_acoes_completas(request):
    """
    Agora: só dispara a tarefa no RabbitMQ.
    Quem chama BRAPI e atualiza o banco é o worker.
    """
    try:
        publicar_tarefa_atualizar_todas_acoes()
        return JsonResponse({
            "ok": True,
            "msg": "Tarefa de atualização de ações enfileirada com sucesso."
        })
    except Exception as e:
        return JsonResponse({
            "ok": False,
            "erro": f"Falha ao enfileirar tarefa: {e}"
        })


@require_POST
def adicionar_acao_completa(request):
    ticker = request.POST.get("busca", "").strip().upper()

    if not ticker:
        return JsonResponse({"ok": False, "erro": "Campo de busca vazio."})

    try:
        publicar_tarefa_atualizar_acao(ticker)
        return JsonResponse({
            "ok": True,
            "msg": f"Tarefa para adicionar/atualizar {ticker} enfileirada."
        })
    except Exception as e:
        return JsonResponse({"ok": False, "erro": str(e)})

@require_GET
def historico_acao(request, ticker):
    """
    Agora: só enfileira a tarefa de buscar e salvar histórico.
    Quem fala com a BRAPI e grava no banco é o worker.
    """
    periodo = request.GET.get("periodo", "1mo")
    print(periodo)

    try:
        publicar_tarefa_historico_acao(ticker, periodo)
        return JsonResponse({
            "ok": True,
            "msg": f"Tarefa para atualizar histórico de {ticker} ({periodo}) enfileirada."
        })
    except Exception as e:
        return JsonResponse({
            "ok": False,
            "erro": f"Falha ao enfileirar tarefa de histórico: {e}"
        })