from datetime import date, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST,require_GET
from django.http import JsonResponse

from tela_cadastro.models import Acao, AcaoHistorico, Monitoramento, Usuario

@login_required(login_url='login')
def home(request):
    monitoramentos = Monitoramento.objects.filter(usuario=request.user, ativo=True).select_related('acao')
    periodos = AcaoHistorico.PeriodoChoices.choices
    context = {
        "monitoramentos": monitoramentos,
        "periodos": periodos,
    }
    return render(request, "home/home.html", context)

@login_required(login_url='login')
def consultar_acoes(request):
    acoes = Acao.objects.all()
     # pega os IDs das ações já monitoradas por este usuário
    monitoradas_ids = Monitoramento.objects.filter(usuario=request.user).values_list('acao_id', flat=True)

    ctx = {
        'acoes': acoes,
        'monitoradas_ids': monitoradas_ids,
    }

    return render(request,'consultar/consultar.html',ctx)

@require_POST
@login_required
def criar_monitoramento(request):
    acao_id = request.POST.get('acao_id')
    preco_alvo = request.POST.get('preco_alvo')
    direcao = request.POST.get('direcao')

    acao = get_object_or_404(Acao, id=acao_id)

    Monitoramento.objects.create(
        usuario=request.user,
        acao=acao,
        preco_alvo=preco_alvo,
        direcao=direcao
    )

    return redirect(request.META.get('HTTP_REFERER', 'listar_acoes'))

@require_GET
def dados_basicos_acoes(request):
    """
    Retorna os dados básicos das ações cadastradas (sem histórico).
    """
    try:
        acoes = Acao.objects.all().order_by("abreviacao")
        dados = [
            {
                "ticker": a.abreviacao,
                "nome": a.nome,
                "valor": a.valor_atual,
                "variacao": a.percentual_mudanca,
                "setor": a.setor or "",
                "market_cap": a.market_cap,
            }
            for a in acoes
        ]
        return JsonResponse({"ok": True, "dados": dados})
    except Exception as e:
        return JsonResponse({"ok": False, "erro": str(e)})



@require_GET
def historico_ou_basico(request, ticker):
    """
    Retorna o histórico da ação filtrando pelo período (ex: 1w, 1mo, 3mo, 6mo, 1y),
    ou, se não houver registros, retorna apenas o valor atual da ação.
    """
    periodo = request.GET.get("periodo", "1mo").lower()
    hoje = date.today()

    # 🔹 Define o intervalo com base no período
    if periodo == "1w":
        data_minima = hoje - timedelta(days=7)
    elif periodo == "1mo":
        data_minima = hoje - timedelta(days=30)
    elif periodo == "3mo":
        data_minima = hoje - timedelta(days=90)
    elif periodo == "6mo":
        data_minima = hoje - timedelta(days=180)
    elif periodo == "1y":
        data_minima = hoje - timedelta(days=365)
    else:
        data_minima = None  # caso inesperado

    try:
        acao = Acao.objects.get(abreviacao__iexact=ticker)
    except Acao.DoesNotExist:
        return JsonResponse({"ok": False, "erro": f"Ação '{ticker}' não encontrada."}, status=404)

    # 🔹 Busca histórico dentro do intervalo (se definido)
    qs = AcaoHistorico.objects.filter(acao=acao)
    if data_minima:
        qs = qs.filter(data__gte=data_minima)

    historicos = qs.order_by("data").values("data", "fechamento", "abertura", "alta", "baixa", "volume")

    if historicos.exists():
        dados = [
            {
                "data": h["data"].strftime("%d/%m/%Y") if h["data"] else "",
                "fechamento": float(h.get("fechamento") or 0),
                "abertura": float(h.get("abertura") or 0),
                "alta": float(h.get("alta") or 0),
                "baixa": float(h.get("baixa") or 0),
                "volume": int(h.get("volume") or 0),
            }
            for h in historicos
        ]
        origem = "historico"
    else:
        # 🔸 Se não há histórico, retorna o dado básico atual
        dados = [{
            "data": acao.atualizado_em.strftime("%d/%m/%Y") if getattr(acao, "atualizado_em", None) else "",
            "fechamento": float(acao.valor_atual or 0),
            "abertura": float(acao.preco_abertura or 0),
            "alta": float(acao.alta_dia or 0),
            "baixa": float(acao.baixa_dia or 0),
            "volume": int(acao.volume or 0),
        }]
        origem = "basico"

    return JsonResponse({
        "ok": True,
        "ticker": acao.abreviacao,
        "periodo": periodo,
        "origem": origem,
        "dados": dados,
    })