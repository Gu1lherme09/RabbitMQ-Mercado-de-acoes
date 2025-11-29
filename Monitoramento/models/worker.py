import os
import time 
import json
import threading
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.acoes_service import AcoesService
from services.alerta_service import AlertaService

from config.rabbitmq_config import RabbitMQConfig
from config.database.database import (
    Database, 
    register_worker, 
    update_worker_heartbeat,  
    set_worker_lider,    
    get_all_workers
)

class Worker:
    
    def __init__(self, worker_id, host='localhost', port=None):
        
        self.worker_id = worker_id
        self.host = host
        self.port = port
        self.is_leader = False
        
        self.start_time = time.time()
        self.running = True
        self.workers_heartbeat = {}
        self.last_leader_heartbeat = time.time()
        
        # RabbitMQ
        print(f"\n [{self.worker_id}] Conectando RabbitMQ...")
        self.rabbitmq_config = RabbitMQConfig()
        self.connection = self.rabbitmq_config.get_connection()
        self.channel = self.connection.channel()
        
        # Canal separado para Telegram (para não bloquear o principal)
        self.telegram_channel = self.connection.channel()
        
        self.rabbitmq_config.setup_exchanges_and_queues(self.channel)
        self.rabbitmq_config.setup_exchanges_and_queues(self.telegram_channel)
        
        self.heartbeat_queue_name = f'heartbeat_{self.worker_id}'
        
        self.channel.queue_declare(
            queue=self.heartbeat_queue_name,
            exclusive=True,
            auto_delete=True
        )
        
        self.channel.queue_bind(
            exchange='election',
            queue=self.heartbeat_queue_name
        )
        
        print(f"[{self.worker_id}] Fila exclusiva criada: {self.heartbeat_queue_name}") 
        
        # PostgreSQL
        print(f" [{self.worker_id}] Conectando PostgreSQL...")
        self.db = Database()
        self.db.connect()
        
        # Registrar worker
        print(f" [{self.worker_id}] Registrando no banco...")
        self.worker_db_id = register_worker(self.db, self.worker_id, self.host, self.port)
        print(f" [{self.worker_id}] Inicializado!\n")
        
        lider_existente = self.db.execute_query(
            "SELECT nome FROM worker WHERE is_lider = TRUE LIMIT 1")
        if not lider_existente:
            print(f" [{self.worker_id}] Nenhum líder encontrado. Iniciando eleição...")
            print(f"   Aguardando 10s para coletar workers...\n")
        
        
    def get_uptime(self):
        return int(time.time() - self.start_time)
    
    def send_heartbeat(self):
        print(f" [{self.worker_id}] Thread de heartbeat iniciada")
        
        while self.running:
            try:
                heartbeat_data = {
                    'tipo': 'heartbeat',
                    'worker_id': self.worker_id,
                    'is_leader': self.is_leader,
                    'timestamp': time.time(), 
                    'uptime': self.get_uptime()
                }
                
                self.channel.basic_publish(
                    exchange='election', 
                    routing_key='',
                    body=json.dumps(heartbeat_data)
                )
                
                update_worker_heartbeat(
                    self.db, 
                    self.worker_id,  # ← Corrigido: nome, não ID
                    self.get_uptime()
                )
                
                print(f" [{self.worker_id}] Heartbeat (Líder: {self.is_leader}, Uptime: {self.get_uptime()}s)")
                
            except Exception as e:
                print(f" [{self.worker_id}] Erro heartbeat: {e}")
            
            time.sleep(5)
        
        print(f" [{self.worker_id}] Thread de heartbeat encerrada")
        
    def process_heartbeat(self, ch, method, properties, body):
        try: 
            data = json.loads(body)
            
            if data.get('tipo') != 'heartbeat':
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            sender_id = data['worker_id']
            
            if sender_id == self.worker_id:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            self.workers_heartbeat[sender_id] = {
                'timestamp': data['timestamp'],
                'is_leader': data.get('is_leader', False),
                'uptime': data.get('uptime', 0)
            }
            
            if data.get('is_leader'):
                self.last_leader_heartbeat = time.time()
                print(f" [{self.worker_id}] Heartbeat do LÍDER: {sender_id}")
            else:
                print(f" [{self.worker_id}] Heartbeat de: {sender_id}")
                
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print(f" [{self.worker_id}] Erro processar heartbeat: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag)
                
    def monitor_leader(self):
        print(f"  [{self.worker_id}] Thread de monitoramento iniciada") 
        
        while self.running:
            try:
                if self.is_leader:
                    time.sleep(2)
                    continue
                
                tempo_sem_lider = time.time() - self.last_leader_heartbeat
                
                if tempo_sem_lider > 15:
                    print(f"\n [{self.worker_id}] LÍDER MORREU!")
                    print(f"   Tempo sem heartbeat: {tempo_sem_lider:.1f}s")
                    print(f"   TODO: Iniciar eleição\n")
                    
                    self.start_election()
                    
                    self.last_leader_heartbeat = time.time()
                    
            except Exception as e:
                print(f" [{self.worker_id}] Erro monitorar: {e}")
                
            time.sleep(2) 
        
        print(f"  [{self.worker_id}] Thread de monitoramento encerrada")
            
    def start(self):  
        print(f"iniciando: {self.worker_id}")
        
        heartbeat_thread = threading.Thread( 
            target=self.send_heartbeat, 
            daemon=True, 
            name=f"Heartbeat-{self.worker_id}"
        )
        heartbeat_thread.start()
        print(f" Thread heartbeat OK")
        
        monitor_thread = threading.Thread(
            target=self.monitor_leader, 
            daemon=True, 
            name=f"Monitor-{self.worker_id}"
        )
        monitor_thread.start()
        print(f" Thread monitor OK")
        
        consumer_thread = threading.Thread(
            target=self.consume_heartbeats, 
            daemon=True,
            name=f"Consumer-{self.worker_id}"
        )
        consumer_thread.start()
        print(f" Thread consumidor OK")
        
        leader_thread = threading.Thread(
            target=self.processar_como_lider, 
            daemon=True,
            name=f"Lider--{self.worker_id}"
        )
        leader_thread.start()
        print(f" Thread líder OK")
       
        print(f"\n Worker {self.worker_id} RODANDO!\n")
        
        try: 
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n Encerrando {self.worker_id}...")
            self.stop()
                
    def consume_heartbeats(self):
        try: 
            self.channel.basic_consume(
                queue=self.heartbeat_queue_name,
                on_message_callback=self.process_heartbeat,
                auto_ack=False
            )
            print(f" [{self.worker_id}] Escutando {self.heartbeat_queue_name}...")
            
            self.channel.start_consuming()
            
        except Exception as e:
            print(f" [{self.worker_id}] Erro consumidor: {e}")
            
    def stop(self):
        self.running = False
        
        try: 
            self.db.execute_update(
                "UPDATE worker SET status = 'offline' WHERE nome = %s",  
                (self.worker_id,)
            )
        except: 
            pass
        
        try: 
            self.connection.close()
            self.db.close()
        except:
            pass
        
        print(f" Worker {self.worker_id} encerrado")
        
    def start_election(self):
        print(f" [{self.worker_id}] Iniciando eleição de líder...")
        
        try: 
            import time 
            time.sleep(3)
            
            candidatos = []
            
            candidatos.append({
                'worker_id': self.worker_id,
                'uptime': self.get_uptime()
            })
            
            for worker_id, info in self.workers_heartbeat.items():
                
                tempo_desde_heartbeat = time.time() - info['timestamp']
                
                if tempo_desde_heartbeat <= 15:
                    candidatos.append({
                        'worker_id': worker_id,
                        'uptime': info['uptime']
                    })
                    print (f"   Candidato: {worker_id} (Uptime: {info['uptime']}s)")
                    
            candidatos.sort(key=lambda x: x['uptime'], reverse=True)
            
            lider_eleito = candidatos[0] 
            
            print(f"\n [{self.worker_id}] LÍDER ELEITO: {lider_eleito['worker_id']} ")
            print(f"(Uptime: {lider_eleito['uptime']}s)\n")       
            print(f"  Total de candidatos: {len(candidatos)}\n ")
            
            from config.database.database import set_worker_lider, log_eleicao
            
            lider_anterior = self.db.execute_query(
                "SELECT id, nome FROM worker WHERE is_lider = TRUE LIMIT 1"
            )
            
            if lider_anterior and len(lider_anterior) > 0:
               lider_anterior_id = lider_anterior[0].get('id') or lider_anterior[0].get('ID')
               lider_anterior_nome = lider_anterior[0].get('nome') or lider_anterior[0].get('NOME')
            else:
               lider_anterior_id = None
               lider_anterior_nome = None
            
            set_worker_lider(self.db, lider_eleito['worker_id'])
            
            novo_lider = self.db.execute_query(
                "SELECT id FROM worker WHERE nome = %s",
            (lider_eleito['worker_id'],)
            )

            if novo_lider and len(novo_lider) > 0:
                novo_lider_id = novo_lider[0].get('id') or novo_lider[0].get('ID')
            else:
                novo_lider_id = None
            
            if novo_lider_id: 
                log_eleicao(
                    self.db,
                    worker_vencedor_id=novo_lider_id,
                    worker_anterior_id=lider_anterior_id,
                    tempo_atividade=lider_eleito['uptime'],
                    tipo_evento='eleicao', 
                    detalhes=f"Eleição iniciada por {self.worker_id}. "
                            f"Líder anterior: {lider_anterior_nome or 'nenhum'}. "
                            f"Novo líder: {lider_eleito['worker_id']} com {lider_eleito['uptime']}s de uptime."
                )
                
            if lider_eleito['worker_id'] == self.worker_id:
                self.is_leader = True
                print(f" [{self.worker_id}] EU SOU O LÍDER AGORA!")
            else:
                self.is_leader = False
                print(f" [{self.worker_id}] Reconheço {lider_eleito['worker_id']} como líder\n")         
                
            self.last_leader_heartbeat = time.time()
            
        except Exception as e:
            print(f" [{self.worker_id}] Erro eleição: {e}")
            import traceback
            traceback.print_exc()
          
    def processar_como_lider(self):
        
        print(f"[{self.worker_id}] Iniciando processamento como LÍDER...")
        
        
        acao_service = AcoesService(self.db, self.channel)
        alerta_service = AlertaService(self.db, self.channel)
        
        while self.running:
            try: 
                
                if not self.is_leader:
                    time.sleep(5)
                    continue
                
                print("Líder processando alertas...")
                
                # Atualiza cotações da API BRAPI
                acao_service.processar_atulizacao()
                
                alerta_service.processar_alertas()
                
                print("Aguardando próximo ciclo...\n")
                time.sleep(60)
                
            except Exception as e:
                print(f"Erro no processamento: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(10)
                
        print(f"[{self.worker_id}] Thread de processamento do líder encerrada")
        
                
        
                    
                
                