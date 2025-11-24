# services/publishers.py
import json
import uuid
import pika

from monitoramento.config.rabbitmq_config import RabbitMQConfig


def publicar_tarefa_atualizar_todas_acoes():
    """
    Publica uma mensagem na fila de cotações para atualizar TODAS as ações.
    """
    config = RabbitMQConfig()
    conn = config.get_connection()
    channel = conn.channel()

    config.setup_exchanges_and_queues(channel)

    payload = {
        "type": "atualizar_todas_acoes",
        "request_id": str(uuid.uuid4()),
    }

    channel.basic_publish(
        exchange="stock_topic",
        routing_key="cotacao.atualizar_todas",
        body=json.dumps(payload),
        properties=pika.BasicProperties(
            delivery_mode=2 
        ),
    )

    conn.close()

def publicar_tarefa_atualizar_acao(ticker: str):
    config = RabbitMQConfig()
    conn = config.get_connection()
    channel = conn.channel()
    config.setup_exchanges_and_queues(channel)

    payload = {
        "type": "atualizar_acao",
        "ticker": ticker,
        "request_id": str(uuid.uuid4()),
    }

    channel.basic_publish(
        exchange="stock_topic",
        routing_key="cotacao.atualizar",
        body=json.dumps(payload),
        properties=pika.BasicProperties(delivery_mode=2),
    )

    conn.close()

def publicar_tarefa_historico_acao(ticker: str, periodo: str = "1mo"):
    """
    Publica tarefa para buscar e salvar histórico de uma ação.
    """
    config = RabbitMQConfig()
    conn = config.get_connection()
    channel = conn.channel()

    config.setup_exchanges_and_queues(channel)

    payload = {
        "type": "historico_acao", 
        "ticker": ticker,
        "periodo": periodo,
        "request_id": str(uuid.uuid4()),
    }

    channel.basic_publish(
        exchange="stock_topic",
        routing_key="cotacao.historico",
        body=json.dumps(payload),
        properties=pika.BasicProperties(delivery_mode=2),
    )

