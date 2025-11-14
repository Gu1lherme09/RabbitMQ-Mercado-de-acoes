# config/test_cloudamqp.py
import sys
import os

# Adicionar pasta pai ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rabbitmq_config import RabbitMQConfig
from dotenv import load_dotenv
import json
import pika

# Carregar .env
load_dotenv()

def test_cloudamqp():
    """Testa conexão com CloudAMQP"""
    
    print("🧪 TESTE: CloudAMQP\n")
    
    try:
        # 1. Criar configuração
        print("📋 Carregando configuração...")
        config = RabbitMQConfig()
        
        # 2. Conectar
        print("🔌 Conectando ao RabbitMQ...")
        connection = config.get_connection()
        channel = connection.channel()
        
        # 3. Configurar infraestrutura
        print("🔧 Configurando exchanges e filas...")
        config.setup_exchanges_and_queues(channel)
        
        # 4. Testar publicação
        print("\n📤 Testando publicação...\n")
        
        message = {
            'tipo': 'teste',
            'mensagem': 'Olá do CloudAMQP!',
            'timestamp': '2024-01-01 10:00:00'
        }
        
        channel.basic_publish(
            exchange='stock_topic',
            routing_key='cotacao.TESTE',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )
        
        print("  ✓ Mensagem publicada com sucesso!")
        
        # 5. Informações úteis
        print("\n📊 Dashboard CloudAMQP:")
        print("  🔗 https://customer.cloudamqp.com/")
        print("  Verifique a fila 'fila_cotacoes'!")
        
        connection.close()
        print("\n✅ TESTE PASSOU! CloudAMQP funcionando!\n")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}\n")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cloudamqp()