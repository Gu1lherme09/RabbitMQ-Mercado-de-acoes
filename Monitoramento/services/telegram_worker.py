import os
import sys
import json
import asyncio

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from dotenv import load_dotenv
load_dotenv()

from telegram_service import TelegramService
from config.rabbitmq_config import RabbitMQConfig
from config.database.database import Database

class TelegramWorker:
    
    def __init__(self): 
        
        self.running = True
        
        self.telegram = TelegramService()
        
        self.rabbitmq_config = RabbitMQConfig()
        self.connection = self.rabbitmq_config.get_connection()
        self.channel = self.connection.channel()
        self.rabbitmq_config.setup_exchanges_and_queues(self.channel)
        
        self.db = Database()
        self.db.connect()
        
        print(f"TelegramWorker inicializado com sucesso.")
        
    def processar_notificacao(self, ch, method, properties, body):
        try: 
            
            data = json.loads(body)
        
            if data.get('tipo') != 'notificacao':
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            notificacao_id = data.get('notificacao_id')
            chat_id = data.get('chat_id')
            mensagem = data.get('mensagem')
            
            print(f"Processando notificacao_id {notificacao_id} para chat_id {chat_id}")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            sucesso = loop.run_until_complete(
                self.telegram.enviar_mensagem(chat_id, mensagem)
            )
            
            if sucesso:
                query = """
                    UPDATE tela_cadastro_notificacaousuario
                    SET enviada_telegram = TRUE
                    WHERE id = %s
                """
                
                self.db.execute_update(query, (notificacao_id,))
                
                print(f"Notificação {notificacao_id} enviada e marcada como enviada.")
            else:
                print(f"Falha ao enviar notificação {notificacao_id}.")
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
        
        except Exception as e:
            print(f"Erro ao processar notificação: {e}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
    def start(self): 
        print("TelegramWorker iniciando consumo de notificações...")
        
        self.channel.basic_consume(
            queue='fila_alertas',
            on_message_callback=self.processar_notificacao,
            auto_ack=False
        )
        
        try: 
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print("TelegramWorker interrompido pelo usuário.")
            self.stop()
            
    def stop(self):
        self.running = False
        if self.connection:
            self.connection.close()
        if self.db:
            self.db.close()
        print("TelegramWorker finalizado.")
        
if __name__ == "__main__":
    worker = TelegramWorker()
    worker.start()                    