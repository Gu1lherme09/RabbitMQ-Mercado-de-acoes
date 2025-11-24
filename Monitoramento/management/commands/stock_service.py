# services/stock_service.py

import os
import requests
from datetime import datetime
from typing import Optional, Dict, List

from tela_cadastro.models import Acao, AcaoHistorico


def safe_get(obj: Optional[Dict], key: str, default=0):
    """
    Retorna valor seguro de um dicionário, evitando None, KeyError e valores vazios.
    """
    if not obj:
        return default
    val = obj.get(key)
    return val if val not in (None, "", "null") else default


def _get_brapi_headers() -> Dict[str, str]:
    """
    Monta os headers de autenticação para a BRAPI, usando a env BRAPI_TOKEN (se existir).
    """
    token = os.getenv("BRAPI_TOKEN")
    return {"Authorization": f"Bearer {token}"} if token else {}


BASE_BRAPI_URL = "https://brapi.dev/api"


def atualizar_acoes_completas() -> Dict:
    """
    Busca lista de ações na BRAPI e preenche o máximo possível de campos no model Acao.

    - Usa /quote/list para obter as ações mais negociadas
    - Para cada ticker, chama /quote/{ticker} para detalhes individuais
    - Cria ou atualiza registros em Acao

    Retorno:
        {
            "ok": True/False,
            "criadas": [tickers],
            "atualizadas": [tickers],
            "falhas": [{ticker: erro}, ...],
            "qtde_processadas": int
        }
    """
    headers = _get_brapi_headers()

    list_url = f"{BASE_BRAPI_URL}/quote/list"
    params = {"limit": 100, "sortBy": "volume", "sortOrder": "desc"}
    response = requests.get(list_url, headers=headers, params=params)

    if response.status_code != 200:
        return {
            "ok": False,
            "erro": f"Falha ao buscar lista ({response.status_code})",
            "detalhe": response.text,
        }

    data = response.json()
    stocks = data.get("stocks", [])

    criadas: List[str] = []
    atualizadas: List[str] = []
    erros: List[Dict[str, str]] = []

    for s in stocks:
        ticker = s.get("stock")
        if not ticker:
            continue

        try:
            detail_url = f"{BASE_BRAPI_URL}/quote/{ticker}"
            detail_resp = requests.get(
                detail_url,
                headers=headers,
                params={"range": "1d"},
            )
            detail_data = detail_resp.json()

            quote = None
            if "results" in detail_data and len(detail_data["results"]) > 0:
                quote = detail_data["results"][0]

            acao, created = Acao.objects.update_or_create(
                abreviacao=ticker,
                defaults={
                    "nome": safe_get(s, "name", ticker),
                    "nome_completo": safe_get(
                        quote, "longName", safe_get(s, "name", ticker)
                    ),
                    "moeda": safe_get(quote, "currency", "BRL"),
                    "valor_atual": safe_get(
                        s, "close", safe_get(quote, "regularMarketPrice", 0)
                    ),
                    "alta_dia": safe_get(quote, "regularMarketDayHigh", 0),
                    "baixa_dia": safe_get(quote, "regularMarketDayLow", 0),
                    "percentual_mudanca": safe_get(
                        s, "change", safe_get(quote, "regularMarketChangePercent", 0)
                    ),
                    "variacao": safe_get(quote, "regularMarketChange", 0),
                    "volume": safe_get(
                        s, "volume", safe_get(quote, "regularMarketVolume", 0)
                    ),
                    "preco_abertura": safe_get(quote, "regularMarketOpen", 0),
                    "preco_anterior": safe_get(
                        quote, "regularMarketPreviousClose", 0
                    ),
                    "faixa_dia": (
                        f"{safe_get(quote, 'regularMarketDayLow', 0)} - "
                        f"{safe_get(quote, 'regularMarketDayHigh', 0)}"
                    ),
                    "market_cap": safe_get(
                        s, "market_cap", safe_get(quote, "marketCap", 0)
                    ),
                    "logo_url": safe_get(s, "logo", safe_get(quote, "logourl", "")),
                    "setor": safe_get(s, "sector", safe_get(quote, "sector", "")),
                    "industria": safe_get(quote, "industry", ""),
                },
            )

            (criadas if created else atualizadas).append(ticker)

        except Exception as e:
            erros.append({ticker: str(e)})

    return {
        "ok": True,
        "criadas": criadas,
        "atualizadas": atualizadas,
        "falhas": erros,
        "qtde_processadas": len(stocks),
    }


def adicionar_acao_completa(nome_ou_ticker: str) -> Dict:
    """
    Busca UMA ação na BRAPI pelo ticker ou nome (match exato ou parcial),
    chama /quote/{ticker} com summaryProfile e salva/atualiza na tabela Acao.

    Retorna dict com:
        - ok: bool
        - msg / erro
        - ticker, nome, acao_id, created
    """
    nome_ou_ticker = (nome_ou_ticker or "").strip()
    if not nome_ou_ticker:
        return {"ok": False, "erro": "Campo de busca vazio."}

    headers = _get_brapi_headers()

    try:
        list_url = f"{BASE_BRAPI_URL}/quote/list"
        params = {"limit": 1000}
        resp = requests.get(list_url, headers=headers, params=params)
        data = resp.json()

        stocks = data.get("stocks", [])
        nome_ou_ticker_lower = nome_ou_ticker.lower()

        stock = next(
            (
                s
                for s in stocks
                if s.get("stock", "").lower() == nome_ou_ticker_lower
            ),
            None,
        )

        if not stock:
            stock = next(
                (
                    s
                    for s in stocks
                    if s.get("name", "").lower() == nome_ou_ticker_lower
                ),
                None,
            )

        if not stock:
            stock = next(
                (
                    s
                    for s in stocks
                    if nome_ou_ticker_lower in s.get("stock", "").lower()
                    or nome_ou_ticker_lower in s.get("name", "").lower()
                ),
                None,
            )

        if not stock:
            return {
                "ok": False,
                "erro": f"Ação '{nome_ou_ticker}' não encontrada na BRAPI.",
            }

        ticker = stock.get("stock")
        nome = stock.get("name", ticker)

        # 2) Busca detalhes + summaryProfile do ticker escolhido
        detail_url = f"{BASE_BRAPI_URL}/quote/{ticker}"
        detail_resp = requests.get(
            detail_url,
            headers=headers,
            params={"range": "1d", "modules": "summaryProfile"},
        )
        detail_data = detail_resp.json()

        quote = detail_data.get("results", [{}])[0]
        profile = quote.get("summaryProfile", {}) or {}

        # 3) Fallback para alguns tickers (ex: BDRs) que não retornam setor/indústria
        if not profile.get("sector") and not ticker.endswith(("11", "12")):
            base_ticker = (
                ticker.replace("34", "")
                .replace("F", "")
                .rstrip()
            )
            if base_ticker != ticker:
                try:
                    resp2 = requests.get(
                        f"{BASE_BRAPI_URL}/quote/{base_ticker}",
                        headers=headers,
                        params={"modules": "summaryProfile"},
                        timeout=10,
                    )
                    data2 = resp2.json()
                    prof2 = (
                        data2.get("results", [{}])[0]
                        .get("summaryProfile", {})
                        or {}
                    )
                    if prof2:
                        profile.update(prof2)
                except Exception:
                    # falha no fallback não deve abortar o fluxo todo
                    pass

        acao, created = Acao.objects.update_or_create(
            abreviacao=ticker,
            defaults={
                "nome": nome,
                "nome_completo": safe_get(quote, "longName", nome),
                "moeda": safe_get(quote, "currency", "BRL"),
                "valor_atual": safe_get(quote, "regularMarketPrice", 0),
                "alta_dia": safe_get(quote, "regularMarketDayHigh", 0),
                "baixa_dia": safe_get(quote, "regularMarketDayLow", 0),
                "percentual_mudanca": safe_get(
                    quote, "regularMarketChangePercent", 0
                ),
                "variacao": safe_get(quote, "regularMarketChange", 0),
                "volume": safe_get(quote, "regularMarketVolume", 0),
                "preco_abertura": safe_get(quote, "regularMarketOpen", 0),
                "preco_anterior": safe_get(
                    quote, "regularMarketPreviousClose", 0
                ),
                "faixa_dia": (
                    f"{safe_get(quote, 'regularMarketDayLow', 0)} - "
                    f"{safe_get(quote, 'regularMarketDayHigh', 0)}"
                ),
                "market_cap": safe_get(quote, "marketCap", 0),
                "logo_url": safe_get(quote, "logourl", ""),
                "setor": safe_get(
                    profile, "sector", safe_get(quote, "sector", "")
                ),
                "industria": safe_get(
                    profile, "industry", safe_get(quote, "industry", "")
                ),
            },
        )

        return {
            "ok": True,
            "msg": f"Ação {ticker} ({nome}) adicionada com sucesso!",
            "ticker": ticker,
            "nome": nome,
            "acao_id": acao.id,
            "created": created,
        }

    except Exception as e:
        return {"ok": False, "erro": str(e)}


def historico_acao(request, ticker):
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
            return ({"ok": False, "erro": f"Ticker '{ticker}' não encontrado na BRAPI."})

        r = results[0]
        prices = r.get("historicalDataPrice", [])
        if not prices:
            return  ({"ok": False, "erro": f"Sem dados para o período '{periodo}'."})

        acao = Acao.objects.filter(abreviacao=ticker).first()
        if not acao:
            return ({"ok": False, "erro": f"Ação '{ticker}' não existe no banco."})

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

        return ({
            "ok": True,
            "msg": f"Histórico ({periodo}) salvo com sucesso — {count_salvos} registros inseridos.",
            "periodo": periodo
        })

    except Exception as e:
        return ({"ok": False, "erro": str(e)})
