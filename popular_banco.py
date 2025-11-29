#!/usr/bin/env python
"""
Script para popular o banco de dados com ações da BRAPI
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Consultor_bolsa.settings')
django.setup()

import requests
from tela_cadastro.models import Acao

def safe_get(obj, key, default=0):
    """Retorna valor seguro de um dicionário"""
    if not obj:
        return default
    val = obj.get(key)
    return val if val not in (None, "", "null") else default

def popular_acoes():
    """Busca ações da BRAPI e popula o banco"""
    token = os.getenv("BRAPI_TOKEN", None)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    base_url = "https://brapi.dev/api"

    print("🔍 Buscando ações na BRAPI...")
    
    # Buscar lista geral
    list_url = f"{base_url}/quote/list"
    params = {"limit": 100, "sortBy": "volume", "sortOrder": "desc"}
    response = requests.get(list_url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"❌ Erro ao buscar lista: {response.status_code}")
        print(response.text)
        return

    data = response.json()
    stocks = data.get("stocks", [])

    print(f"📊 Encontradas {len(stocks)} ações")
    print("💾 Salvando no banco...")

    criadas = 0
    atualizadas = 0
    erros = 0

    for i, s in enumerate(stocks, 1):
        ticker = s.get("stock")
        
        try:
            # Buscar detalhes
            detail_url = f"{base_url}/quote/{ticker}"
            detail_resp = requests.get(detail_url, headers=headers, params={"range": "1d"})
            detail_data = detail_resp.json()

            quote = None
            if "results" in detail_data and len(detail_data["results"]) > 0:
                quote = detail_data["results"][0]

            # Criar ou atualizar
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

            if created:
                criadas += 1
                print(f"  ✅ [{i}/{len(stocks)}] {ticker} - Criada")
            else:
                atualizadas += 1
                print(f"  🔄 [{i}/{len(stocks)}] {ticker} - Atualizada")

        except Exception as e:
            erros += 1
            print(f"  ❌ [{i}/{len(stocks)}] {ticker} - Erro: {e}")

    print("\n" + "="*60)
    print("📊 RESUMO:")
    print(f"  ✅ Criadas: {criadas}")
    print(f"  🔄 Atualizadas: {atualizadas}")
    print(f"  ❌ Erros: {erros}")
    print(f"  📈 Total processadas: {len(stocks)}")
    print("="*60)

if __name__ == '__main__':
    popular_acoes()
