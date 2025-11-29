import os
import time 
import requests
import json 

class AcoesService:
    
    def __init__(self, db, channel):
        
        self.db = db
        self.channel = channel
        self.brapi_token = os.getenv('BRAPI_TOKEN', '')
        self.brapi_url = os.getenv('BRAPI_URL', 'https://brapi.dev/api/quot')
        
        
        self.hearders = {}
        
        if self.brapi_token:
            self.hearders['Authorization'] = f'Bearer {self.brapi_token}'
            
    def buscar_acoes_monitoradas(self):
        query = """
        SELECT DISTINCT a.abreviacao 
        FROM tela_cadastro_acao a
        INNER JOIN tela_cadastro_monitoramento m ON a.id = m.acao_id
        WHERE m.ativo = TRUE;
        """
        
        result = self.db.execute_query(query)
        
        if not result:
            return []
        
        simbolos = [row.get('abreviacao') or row.get('ABREVIACAO') for row in result]        
        return simbolos
    
    def buscar_cotacoes(self, simbolos):
        if not simbolos:
            return {}
        
        tikers = ','.join(simbolos)
        
        try:
            url = f"{self.brapi_url}/{tikers}"
            response = requests.get(url, headers=self.hearders, timeout=10)
            
            if response.status_code != 200:
                print(f"Erro ao buscar cotações: {response.status_code} - {response.text}")
                return {}
            
            data = response.json()
            results = data.get('results', [])
  
            cotacoes = {}
            for stock in results: 
                symbol = stock.get('symbol')
                if symbol:
                    cotacoes[symbol] = stock
                    
            return cotacoes
            
        except Exception as e:
            print(f"Erro ao buscar cotações: {e}")
            return {}    
        
    def atualizar_acao(self, simbolo, dados):
        query = """
            UPDATE tela_cadastro_acao SET
                valor_atual = %s,
                alta_dia = %s,
                baixa_dia = %s,
                percentual_mudanca = %s,
                variacao = %s,
                volume = %s,
                preco_abertura = %s,
                preco_anterior = %s,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE abreviacao = %s
        """
        
        params = (
            dados.get('regularMarketPrice', 0),
            dados.get('regularMarketDayHigh', 0),
            dados.get('regularMarketDayLow', 0),
            dados.get('regularMarketChangePercent', 0),
            dados.get('regularMarketChange', 0),
            dados.get('regularMarketVolume', 0),
            dados.get('regularMarketOpen', 0),
            dados.get('regularMarketPreviousClose', 0),
            simbolo
        )
        
        self.db.execute_update(query, params)
        
    def publicar_cotacao(self, simbolo, dados): 
        
        mensagem = {
            'tipo': 'cotacao_atualizada', 
            'simbolo': simbolo,
            'preco': dados.get('regularMarketPrice', 0),
            'variacao': dados.get('regularMarketChangePercent', 0),
            'timestamp': time.time()
        }  
        
        self.channel.basic_publish(
            exchange='stock_topic',
            routing_key=f'cotacao.{simbolo}',
            body=json.dumps(mensagem),
        )
        
    def processar_atulizacao(self): 
        print("ATUALIZANDO COTAÇÕES")
        
        simbolos = self.buscar_acoes_monitoradas()
        
        if not simbolos:
            print("Nenhuma ação monitorada encontrada.")
            return 0
        
        print(f"Ações monitoradas: {', '.join(simbolos)}")
        
        
        print("Buscando cotações da api...")
  
        cotacoes = self.buscar_cotacoes(simbolos)
        
        if not cotacoes:
            print("Nenhuma cotação retornada pela API.")
            return 0
        
        print ("Atualizando ações no banco de dados ...")
        
        count = 0 
        for simbolo, dados in cotacoes.items():
            try: 
                self.atualizar_acao(simbolo, dados)
                self.publicar_cotacao(simbolo, dados)
                
                preco = dados.get('regularMarketPrice', 0)
                var = dados.get('regularMarketChangePercent', 0)
                print(f" {simbolo}: R$ {preco} ({var}%)")
                
                count += 1
            except Exception as e:
                print(f"Erro ao processar atualização para {simbolo}: {e}")
                
        print(f"Cotações atualizadas: {count}")
        return count        
        
           