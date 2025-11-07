import os
from django.http import JsonResponse
import requests
from datetime import datetime
from typing import Optional, Dict
from django.conf import settings
from django.views.decorators.http import require_GET

from tela_cadastro.models import Acao, AcaoHistorico, Dividendo, EmpresaPerfil


# Função genérica para fazer GET na API do brapi
def _brapi_get(path: str, params: Optional[Dict] = None):
    """
    Wrapper genérico para acessar a API brapi.dev
    Usa o token do settings (se existir)
    """
    if params is None:
        params = {}

    base_url = "https://brapi.dev/api"
    headers = {}

    # adiciona token se estiver definido
    if hasattr(settings, "BRAPI_TOKEN") and settings.BRAPI_TOKEN:
        headers["Authorization"] = f"Bearer {settings.BRAPI_TOKEN}"

    url = f"{base_url}/{path.lstrip('/')}"
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        raise Exception(f"Erro {response.status_code}: {response.text}")

    return response.json()

def atualizar_essencial():
    """
    Atualiza informações básicas de todas as ações cadastradas no banco.
    Usa /api/quote/{tickers} da Brapi.
    """
    tickers = [a.abreviacao for a in Acao.objects.all()]
    if not tickers:
        print("⚠️ Nenhuma ação cadastrada.")
        return

    # Se tiver MUITOS tickers, depois dá pra fatiar em grupos.
    tickers_str = ",".join(tickers)
    print(f"🔄 Atualizando dados essenciais de {len(tickers)} ações...")

    try:
        data = _brapi_get(f"/quote/{tickers_str}")
        results = data.get("results", [])

        for r in results:
            symbol = r.get("symbol")
            if not symbol:
                continue

            Acao.objects.update_or_create(
                abreviacao=symbol,
                defaults={
                    "nome": r.get("shortName") or "",
                    "nome_completo": r.get("longName") or "",
                    "moeda": r.get("currency", "BRL"),

                    "valor_atual": r.get("regularMarketPrice") or 0,
                    "alta_dia": r.get("regularMarketDayHigh") or 0,
                    "baixa_dia": r.get("regularMarketDayLow") or 0,
                    "percentual_mudanca": r.get("regularMarketChangePercent") or 0,
                    "variacao": r.get("regularMarketChange") or 0,
                    "preco_abertura": r.get("regularMarketOpen") or 0,
                    "preco_anterior": r.get("regularMarketPreviousClose") or 0,
                    "volume": r.get("regularMarketVolume") or 0,
                    "market_cap": r.get("marketCap") or 0,
                    "faixa_dia": r.get("regularMarketDayRange") or "",

                    "setor": r.get("sector") or "",
                    "industria": r.get("industry") or "",
                    "logo_url": r.get("logourl") or "",

                    "atualizado_em": datetime.now(),
                },
            )

        print("✅ Atualização essencial concluída!")

    except Exception as e:
        print(f"❌ Erro ao atualizar essencial: {e}")

def buscar_detalhes_acao(ticker: str):
    """
    Busca dados completos de UMA ação:
    - cotação
    - perfil da empresa (summaryProfile)
    - dividendos (dividendsData)
    """
    try:
        print(f"🔍 Buscando dados completos de {ticker}...")

        data = _brapi_get(
            f"/quote/{ticker}",
            params={
                "fundamental": "true",
                "dividends": "true",
                "modules": "summaryProfile",
            },
        )

        results = data.get("results", [])
        if not results:
            raise RuntimeError("Ticker não encontrado na Brapi")

        r = results[0]

        # --- Ação (dados principais) ---
        acao, _ = Acao.objects.update_or_create(
            abreviacao=r.get("symbol"),
            defaults={
                "nome": r.get("shortName") or "",
                "nome_completo": r.get("longName") or "",
                "moeda": r.get("currency", "BRL"),

                "valor_atual": r.get("regularMarketPrice") or 0,
                "alta_dia": r.get("regularMarketDayHigh") or 0,
                "baixa_dia": r.get("regularMarketDayLow") or 0,
                "percentual_mudanca": r.get("regularMarketChangePercent") or 0,
                "variacao": r.get("regularMarketChange") or 0,
                "preco_abertura": r.get("regularMarketOpen") or 0,
                "preco_anterior": r.get("regularMarketPreviousClose") or 0,
                "volume": r.get("regularMarketVolume") or 0,
                "market_cap": r.get("marketCap") or 0,
                "faixa_dia": r.get("regularMarketDayRange") or "",

                "setor": r.get("sector") or "",
                "industria": r.get("industry") or "",
                "logo_url": r.get("logourl") or "",

                "atualizado_em": datetime.now(),
            },
        )

        # --- Perfil da Empresa (summaryProfile) ---
        profile = (r.get("summaryProfile") or {})  # depende do módulo
        EmpresaPerfil.objects.update_or_create(
            acao=acao,
            defaults={
                "endereco": profile.get("address1") or "",
                "cidade": profile.get("city") or "",
                "estado": profile.get("state") or "",
                "pais": profile.get("country") or "",
                "setor": profile.get("sector") or r.get("sector") or "",
                "industria": profile.get("industry") or r.get("industry") or "",
                "funcionarios": profile.get("fullTimeEmployees") or None,
                "descricao_longa": profile.get("longBusinessSummary") or "",
                "site": profile.get("website") or "",
                "telefone": profile.get("phone") or "",
            },
        )

        # --- Dividendos (dividendsData) ---
        for d in r.get("dividendsData", []):
            data_pag = d.get("paymentDate")
            # cuidado: pode vir None
            Dividendo.objects.update_or_create(
                acao=acao,
                data_pagamento=data_pag,
                defaults={
                    "tipo": d.get("label"),
                    "valor": d.get("amount") or 0,
                    "descricao": d.get("assetIssued") or "",
                    "ultima_data_prior": d.get("lastDatePrior"),
                    "aprovado_em": d.get("approvedOn"),
                    "isin_code": d.get("isinCode"),
                    "observacoes": d.get("notes"),
                },
            )

        print(f"✅ {ticker} atualizado com sucesso.")
        return acao

    except Exception as e:
        print(f"❌ Erro ao buscar detalhes de {ticker}: {e}")
        return None

def buscar_historico_acao(ticker: str, periodo: str = "1mo"):
    """
    Busca histórico de preços de uma ação para o período informado.
    Ex: periodo="1mo", "6mo", "1y", "5y", "max"
    """
    try:
        data = _brapi_get(
            f"/quote/{ticker}",
            params={
                "range": periodo,
                "interval": "1d",
            },
        )

        results = data.get("results", [])
        if not results:
            print(f"⚠️ Nenhum resultado de histórico para {ticker}.")
            return

        r = results[0]
        prices = r.get("historicalDataPrice", [])
        if not prices:
            print(f"⚠️ Não há historicalDataPrice para {ticker}.")
            return

        acao = Acao.objects.get(abreviacao=ticker)

        for p in prices:
            dt = datetime.fromtimestamp(p["date"]).date()

            AcaoHistorico.objects.update_or_create(
                acao=acao,
                data=dt,
                periodo=periodo,
                defaults={
                    "abertura": p.get("open") or 0,
                    "fechamento": p.get("close") or 0,
                    "alta": p.get("high") or 0,
                    "baixa": p.get("low") or 0,
                    "volume": p.get("volume") or 0,
                },
            )

        print(f"📊 Histórico de {ticker} ({periodo}) atualizado: {len(prices)} pontos.")

    except Exception as e:
        print(f"⚠️ Erro ao buscar histórico de {ticker}: {e}")


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
                    "nome": s.get("name") or ticker,
                    "nome_completo": quote.get("longName") if quote else s.get("name"),
                    "moeda": quote.get("currency") if quote else "BRL",
                    "valor_atual": s.get("close") or (quote.get("regularMarketPrice") if quote else 0),
                    "alta_dia": quote.get("regularMarketDayHigh") if quote else 0,
                    "baixa_dia": quote.get("regularMarketDayLow") if quote else 0,
                    "percentual_mudanca": s.get("change") or (quote.get("regularMarketChangePercent") if quote else 0),
                    "variacao": quote.get("regularMarketChange") if quote else 0,
                    "volume": s.get("volume") or (quote.get("regularMarketVolume") if quote else 0),
                    "preco_abertura": quote.get("regularMarketOpen") if quote else 0,
                    "preco_anterior": quote.get("regularMarketPreviousClose") if quote else 0,
                    "faixa_dia": f"{quote.get('regularMarketDayLow', 0)} - {quote.get('regularMarketDayHigh', 0)}" if quote else "",
                    "market_cap": s.get("market_cap") or (quote.get("marketCap") if quote else 0),
                    "logo_url": s.get("logo") or (quote.get("logourl") if quote else ""),
                    "setor": s.get("sector") or (quote.get("sector") if quote else ""),
                    "industria": quote.get("industry") if quote else "",
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