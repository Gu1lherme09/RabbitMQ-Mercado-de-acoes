import os , requests
from django.http import JsonResponse
from datetime import datetime
from typing import Optional, Dict
from django.conf import settings
from django.views.decorators.http import require_POST,require_GET

from tela_cadastro.models import Acao, AcaoHistorico

def safe_get(obj, key, default=0):
    """
    Retorna valor seguro de um dicionário, evitando None, KeyError e valores vazios.
    """
    if not obj:
        return default
    val = obj.get(key)
    return val if val not in (None, "", "null") else default

def atualizar_acoes_completas(request):
    """
    Busca lista de ações na BRAPI e preenche o máximo possível de campos no model Acao.
    Usa /quote/list para base e /quote/{ticker} para detalhes individuais.
    """
    token = os.getenv("BRAPI_TOKEN", None)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    base_url = "https://brapi.dev/api"

    # 1️⃣ Buscar lista geral (máximo 100 ações por página)
    list_url = f"{base_url}/quote/list"
    params = {"limit": 100, "sortBy": "volume", "sortOrder": "desc"}
    response = requests.get(list_url, headers=headers, params=params)

    if response.status_code != 200:
        return JsonResponse({
            "ok": False,
            "erro": f"Falha ao buscar lista ({response.status_code})",
            "detalhe": response.text,
        })

    data = response.json()
    stocks = data.get("stocks", [])

    criadas, atualizadas, erros = [], [], []

    # 2️⃣ Iterar sobre cada ação e buscar detalhes
    for s in stocks:
        ticker = s.get("stock")
        try:
            # Buscar detalhes
            detail_url = f"{base_url}/quote/{ticker}"
            detail_resp = requests.get(detail_url, headers=headers, params={"range": "1d"})
            detail_data = detail_resp.json()

            quote = None
            if "results" in detail_data and len(detail_data["results"]) > 0:
                quote = detail_data["results"][0]

            # Atualizar ou criar
            acao, created = Acao.objects.update_or_create(
                abreviacao=ticker,
                defaults={
                    "nome": safe_get(s, "name", ticker),
                    "nome_completo": safe_get(quote, "longName", safe_get(s, "name", ticker)),
                    "moeda": safe_get(quote, "currency", "BRL"),
                    "valor_atual": safe_get(s, "close", safe_get(quote, "regularMarketPrice", 0)),
                    "alta_dia": safe_get(quote, "regularMarketDayHigh", 0),
                    "baixa_dia": safe_get(quote, "regularMarketDayLow", 0),
                    "percentual_mudanca": safe_get(s, "change", safe_get(quote, "regularMarketChangePercent", 0)),
                    "variacao": safe_get(quote, "regularMarketChange", 0),
                    "volume": safe_get(s, "volume", safe_get(quote, "regularMarketVolume", 0)),
                    "preco_abertura": safe_get(quote, "regularMarketOpen", 0),
                    "preco_anterior": safe_get(quote, "regularMarketPreviousClose", 0),
                    "faixa_dia": f"{safe_get(quote, 'regularMarketDayLow', 0)} - {safe_get(quote, 'regularMarketDayHigh', 0)}",
                    "market_cap": safe_get(s, "market_cap", safe_get(quote, "marketCap", 0)),
                    "logo_url": safe_get(s, "logo", safe_get(quote, "logourl", "")),
                    "setor": safe_get(s, "sector", safe_get(quote, "sector", "")),
                    "industria": safe_get(quote, "industry", ""),
                },
            )

            (criadas if created else atualizadas).append(ticker)

        except Exception as e:
            erros.append({ticker: str(e)})

    return JsonResponse({
        "ok": True,
        "criadas": criadas,
        "atualizadas": atualizadas,
        "falhas": erros,
        "qtde_processadas": len(stocks),
    })


@require_POST
def adicionar_acao_completa(request):
    nome_ou_ticker = request.POST.get("busca", "").strip()

    if not nome_ou_ticker:
        return JsonResponse({"ok": False, "erro": "Campo de busca vazio."})

    token = os.getenv("BRAPI_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    base_url = "https://brapi.dev/api"

    try:
        # 1️⃣ Buscar lista geral
        list_url = f"{base_url}/quote/list"
        params = {"limit": 1000}
        resp = requests.get(list_url, headers=headers, params=params)
        data = resp.json()

        stocks = data.get("stocks", [])

        nome_ou_ticker_lower = nome_ou_ticker.lower()

        # 🔹 1️⃣ Busca ticker exato
        stock = next(
            (s for s in stocks if s.get("stock", "").lower() == nome_ou_ticker_lower),
            None
        )

        # 🔹 2️⃣ Se não achar, busca nome exato
        if not stock:
            stock = next(
                (s for s in stocks if s.get("name", "").lower() == nome_ou_ticker_lower),
                None
            )

        # 🔹 3️⃣ Se ainda não achar, busca correspondência parcial (fallback)
        if not stock:
            stock = next(
                (s for s in stocks if nome_ou_ticker_lower in s.get("stock", "").lower() 
                or nome_ou_ticker_lower in s.get("name", "").lower()),
                None
            )

        if not stock:
            return JsonResponse({"ok": False, "erro": f"Ação '{nome_ou_ticker}' não encontrada na BRAPI."})

        ticker = stock.get("stock")
        nome = stock.get("name", ticker)

        # Busca detalhes completos
        detail_url = f"{base_url}/quote/{ticker}"
        detail_resp = requests.get(
            detail_url,
            headers=headers,
            params={"range": "1d", "modules": "summaryProfile"}
        )
        detail_data = detail_resp.json()

        quote = detail_data.get("results", [{}])[0]
        profile = quote.get("summaryProfile", {})

        if not profile.get("sector") and not ticker.endswith(("11", "12")):
            base_ticker = (
                ticker.replace("34", "")
                    .replace("F", "")
                    .rstrip()
            )
            if base_ticker != ticker:
                try:
                    resp2 = requests.get(
                        f"{base_url}/quote/{base_ticker}",
                        headers=headers,
                        params={"modules": "summaryProfile"},
                        timeout=10
                    )
                    data2 = resp2.json()
                    prof2 = data2.get("results", [{}])[0].get("summaryProfile", {})
                    if prof2:
                        profile.update(prof2)
                except Exception as e:
                    print(f"⚠️ Falha no fallback global: {e}")

        acao, created = Acao.objects.update_or_create(
            abreviacao=ticker,
            defaults={
                "nome": nome,
                "nome_completo": safe_get(quote, "longName", nome),
                "moeda": safe_get(quote, "currency", "BRL"),
                "valor_atual": safe_get(quote, "regularMarketPrice", 0),
                "alta_dia": safe_get(quote, "regularMarketDayHigh", 0),
                "baixa_dia": safe_get(quote, "regularMarketDayLow", 0),
                "percentual_mudanca": safe_get(quote, "regularMarketChangePercent", 0),
                "variacao": safe_get(quote, "regularMarketChange", 0),
                "volume": safe_get(quote, "regularMarketVolume", 0),
                "preco_abertura": safe_get(quote, "regularMarketOpen", 0),
                "preco_anterior": safe_get(quote, "regularMarketPreviousClose", 0),
                "faixa_dia": f"{safe_get(quote, 'regularMarketDayLow', 0)} - {safe_get(quote, 'regularMarketDayHigh', 0)}",
                "market_cap": safe_get(quote, "marketCap", 0),
                "logo_url": safe_get(quote, "logourl", ""),
                "setor": safe_get(profile, "sector", safe_get(quote, "sector", "")),
                "industria": safe_get(profile, "industry", safe_get(quote, "industry", "")),
            },
        )

        return JsonResponse({
            "ok": True,
            "msg": f"Ação {ticker} ({nome}) adicionada com sucesso!",
            "ticker": ticker,
            "nome": nome,
            "acao_id": acao.id
        })

    except Exception as e:
        return JsonResponse({"ok": False, "erro": str(e)})

@require_GET
def historico_acao(request, ticker):
    """
    Busca o histórico de preços de uma ação da BRAPI e salva no banco.
    """
    periodo = request.GET.get("periodo", "1mo")
    token = os.getenv("BRAPI_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    base_url = "https://brapi.dev/api"

    # Corrige o ticker automaticamente
    ticker_brapi = ticker if "." in ticker else f"{ticker}.SA"

    try:
        url = f"{base_url}/quote/{ticker_brapi}"
        params = {"range": periodo, "interval": "1d"}
        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()

        results = data.get("results", [])
        if not results:
            return JsonResponse({"ok": False, "erro": f"Ticker '{ticker}' não encontrado na BRAPI."})

        r = results[0]
        prices = r.get("historicalDataPrice", [])
        if not prices:
            return JsonResponse({"ok": False, "erro": f"Sem dados para o período '{periodo}'."})

        acao = Acao.objects.filter(abreviacao=ticker).first()
        if not acao:
            return JsonResponse({"ok": False, "erro": f"Ação '{ticker}' não existe no banco."})

        count_salvos = 0
        for p in prices:
            data_p = datetime.fromtimestamp(p["date"]).date()
            _, created = AcaoHistorico.objects.update_or_create(
                acao=acao,
                data=data_p,
                periodo=periodo,
                defaults={
                    "abertura": safe_get(p, "open", 0),
                    "fechamento": safe_get(p, "close", 0),
                    "alta": safe_get(p, "high", 0), 
                    "baixa": safe_get(p, "low", 0),
                    "volume": safe_get(p, "volume", 0),
                    "variacao": safe_get(p, "close", 0) - safe_get(p, "open", 0),
                }
            ) 

            if created:
                count_salvos += 1

        return JsonResponse({
            "ok": True,
            "msg": f"Histórico ({periodo}) salvo com sucesso — {count_salvos} registros inseridos.",
            "periodo": periodo
        })

    except Exception as e:
        return JsonResponse({"ok": False, "erro": str(e)})