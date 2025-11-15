import sys
import os

# Adicionar pasta pai ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Carregar .env
from dotenv import load_dotenv

load_dotenv()

# Importar m�dulos
from config.rabbitmq_config import RabbitMQConfig
import json
import pika


def test_connection():
    """Testa conex�o b�sica com RabbitMQ"""
    print("\n" + "="*60)
    print("?? TESTE 1: Conex�o com RabbitMQ")
    print("="*60)
    
    try:
        config = RabbitMQConfig()
        connection = config.get_connection()
        connection.close()
        print("? Teste de conex�o PASSOU!\n")
        return True
    except Exception as e:
        print(f"? Teste de conex�o FALHOU: {e}\n")
        return False


def test_setup():
    """Testa cria��o de exchanges e filas"""
    print("="*60)
    print("?? TESTE 2: Cria��o de Exchanges e Filas")
    print("="*60)
    
    try:
        config = RabbitMQConfig()
        connection = config.get_connection()
        channel = connection.channel()
        
        config.setup_exchanges_and_queues(channel)
        
        connection.close()
        print("? Teste de setup PASSOU!\n")
        return True
    except Exception as e:
        print(f"? Teste de setup FALHOU: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_publish_consume():
    """Testa publicação e consumo de mensagens"""
    print("="*60)
    print("🧪 TESTE 3: Publicação e Consumo")
    print("="*60)
    
    try:
        config = RabbitMQConfig()
        connection = config.get_connection()
        channel = connection.channel()
        
        # Configurar (mas não fechar a conexão!)
        config.setup_exchanges_and_queues(channel)
        
        # Mensagem de teste
        test_message = {
            'symbol': 'PETR4',
            'price': 28.50,
            'change': 0.35,
            'timestamp': '2025-01-15 10:00:00'
        }
        
        # Publicar
        print("\n📤 Publicando mensagem...")
        channel.basic_publish(
            exchange='stock_topic',
            routing_key='cotacao.PETR4',
            body=json.dumps(test_message),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )
        print(f"   ✓ Publicado: {test_message}")
        
        # IMPORTANTE: Aguardar um pouco para mensagem ser roteada
        import time
        time.sleep(0.5)
        
        # Consumir (USANDO O MESMO CANAL!)
        print("\n📥 Consumindo mensagem...")
        method, properties, body = channel.basic_get(
            queue='fila_cotacoes',
            auto_ack=True
        )
        
        if method:
            received = json.loads(body)
            print(f"   ✓ Recebido: {received}")
            
            if received == test_message:
                print("\n✅ Teste de publicação/consumo PASSOU!")
                print("   Mensagem enviada = Mensagem recebida ✓\n")
                connection.close()
                return True
            else:
                print("\n⚠️  Mensagens diferentes!")
                print(f"   Enviada: {test_message}")
                print(f"   Recebida: {received}\n")
                connection.close()
                return False
        else:
            print("   ⚠️  Nenhuma mensagem na fila")
            print("   (A mensagem foi publicada mas não chegou na fila)\n")
            connection.close()
            return False
        
    except Exception as e:
        print(f"❌ Teste de publicação/consumo FALHOU: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Executa todos os testes"""
    print("\n" + "??"*30)
    print("TESTE COMPLETO DA CONFIGURA��O RABBITMQ")
    print("??"*30 + "\n")
    
    # Executar testes
    test1 = test_connection()
    test2 = test_setup()
    test3 = test_publish_consume()
    
    # Resultado final
    print("\n" + "="*60)
    print("?? RESULTADO FINAL")
    print("="*60)
    print(f"Teste 1 (Conex�o):          {'? PASSOU' if test1 else '? FALHOU'}")
    print(f"Teste 2 (Setup):            {'? PASSOU' if test2 else '? FALHOU'}")
    print(f"Teste 3 (Publicar/Consumir):{'? PASSOU' if test3 else '? FALHOU'}")
    print("="*60)
    
    if test1 and test2 and test3:
        print("\n?? TODOS OS TESTES PASSARAM!")
        print("\n?? Pr�ximos Passos:")
        print("1. Acesse: https://customer.cloudamqp.com/")
        print("2. Veja as filas criadas no dashboard")
        print("3. Monitore mensagens em tempo real")
        print("\n? Configura��o RabbitMQ completa e funcionando!\n")
    else:
        print("\n??  ALGUNS TESTES FALHARAM!")
        print("Verifique os erros acima e corrija.\n")


if __name__ == "__main__":
    main()