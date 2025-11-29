import json 
import time 

class AlertaService: 
    
    def __init__(self,db,channel): 
        self.db = db
        self.channel = channel


    def buscar_alertas_ativos(self):
   
        query = """
            SELECT 
               m.id as alerta_id,
               'preco' as tipo_alerta,
                CASE 
                    WHEN m.direcao = 'acima' THEN '>'
                    WHEN m.direcao = 'acima_ou_igual' THEN '>='
                    WHEN m.direcao = 'abaixo' THEN '<'
                    WHEN m.direcao = 'abaixo_ou_igual' THEN '<='
                END as operador,
                m.preco_alvo as valor_referencia,
                u.id as usuario_id,
                u.email,
                u.chat_id,
                a.id as acao_id,
                a.abreviacao,
                a.nome as acao_nome,
                a.valor_atual,
                FALSE as disparado  
            FROM tela_cadastro_monitoramento m
            INNER JOIN tela_cadastro_usuario u ON m.usuario_id = u.id
            INNER JOIN tela_cadastro_acao a ON m.acao_id = a.id
            WHERE m.ativo = TRUE
        """
        result = self.db.execute_query(query)
        return result or []

    def verificar_condicao(self, valor_atual, operador, valor_referencia):
        if operador == '>':
            return valor_atual > valor_referencia
        elif operador == '>=':
            return valor_atual >= valor_referencia
        elif operador == '<':
            return valor_atual < valor_referencia
        elif operador == '<=':
            return valor_atual <= valor_referencia
        elif operador == '=':
             return abs(valor_atual - valor_referencia) < 0.01
         
        return False
    
    def criar_notificacao(self, alerta): 
        titulo = f"🚨 Alerta: {alerta['abreviacao']}"
        
        mensagem = (
            f"*{alerta['acao_nome']} ({alerta['abreviacao']})*\n\n"
            f"Preço Atual: R$ {alerta['valor_atual']:.2f}\n"
            f"Condição: {alerta['operador']} R$ {alerta['valor_referencia']:.2f}\n\n"
            f"_Seu alerta foi disparado!_"
        )
        
        query = """
            INSERT INTO tela_cadastro_notificacaousuario
            (usuario_id, titulo, mensagem, tipo, lida, enviada_telegram, criado_em)
            VALUES (%s, %s, %s, 'alerta', FALSE, FALSE, CURRENT_TIMESTAMP)
            RETURNING id;
            """
        
        params = (
            alerta['usuario_id'],
            titulo,
            mensagem
        )    
        
        result = self.db.execute_query(query, params)
        
        if result and len(result) > 0:
            return result[0].get('id') or result[0].get('ID')
        
        return None
    
    def marcar_alerta_disparado(self, alerta_id):
        # Não desativar o monitoramento, deixar ativo para continuar monitorando
        # Se quiser desativar, descomente a linha abaixo:
        # query = "UPDATE tela_cadastro_monitoramento SET ativo = FALSE WHERE id = %s"
        # self.db.execute_update(query, (alerta_id,))
        pass
        
    def publicar_notificacao(self, notificacao_id, usuario_id, chat_id, mensagem):
        
        if not chat_id: 
            print(f"Usuário {usuario_id} não possui chat_id Telegram configurado.")
            return 
        
        payload = {
            'tipo': 'notificacao',
            'notificacao_id': notificacao_id,
            'usuario_id': usuario_id,
            'chat_id': chat_id,
            'mensagem': mensagem,
            'timestamp': time.time()
        }
        
        self.channel.basic_publish(
            exchange='stock_topic',
            routing_key='alerta.notificacao',
            body=json.dumps(payload)
        )
        
        print(f" Notificação enviada para fila")    

    def processar_alertas(self):
        print("Verificando alertas")
        
        alertas = self.buscar_alertas_ativos()
        
        if not alertas:
            print(" Nenhum alerta ativo encontrado.")
            return 0
        
        print(f" {len(alertas)} alertas ativos encontrados.")
        
        disparados = 0
        
        for alerta in alertas:
            simbolo = alerta.get('abreviacao') or alerta.get('ABREVIACAO')
            acao_id = alerta.get('acao_id') or alerta.get('ACAO_ID')
            operador = alerta.get('operador') or alerta.get('OPERADOR')
            valor_ref = alerta.get('valor_referencia') or alerta.get('VALOR_REFERENCIA')
            
            # 🔥 BUSCAR VALOR ATUAL DIRETO DO BANCO (atualizado)
            query_valor = "SELECT valor_atual FROM tela_cadastro_acao WHERE id = %s"
            resultado_valor = self.db.execute_query(query_valor, (acao_id,))
            
            if not resultado_valor:
                print(f"⚠️ Ação {simbolo} não encontrada no banco")
                continue
                
            valor_atual = resultado_valor[0].get('valor_atual') or resultado_valor[0].get('VALOR_ATUAL')
            
            print(f"🔍 {simbolo}: R$ {valor_atual:.2f} {operador} R$ {valor_ref:.2f}")
            
            if self.verificar_condicao(valor_atual, operador, valor_ref):
                print(f"Alerta Disparado")
                
                notif_id = self.criar_notificacao(alerta)
                
                if notif_id:
                    alerta_id = alerta.get('alerta_id') or alerta.get('ALERTA_ID')
                    self.marcar_alerta_disparado(alerta_id)
                    
                    usuario_id = alerta.get('usuario_id') or alerta.get('USUARIO_ID')
                    chat_id = alerta.get('chat_id') or alerta.get('CHAT_ID')
                    email = alerta.get('email') or alerta.get('EMAIL')
                    
                    mensagem = (
                        f"*{simbolo}* atingiu R$ {valor_atual:.2f}\n"
                        f"Condição: {operador} R$ {valor_ref:.2f}"
                    )
                        
                    self.publicar_notificacao(notif_id, usuario_id, chat_id, mensagem)     
                    
                    print(f"Usuário:{email}")
                    disparados += 1
                else:
                    print("Erro ao criar notificação.")   
            else:
                print("Condição não atendida.")    
                
        print(f"Alertas disparados: {disparados}")
        
        return disparados             
        
