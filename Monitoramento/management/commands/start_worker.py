import json
import os
import socket
import time

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction


from monitoramento.config.rabbitmq_config import RabbitMQConfig
from monitoramento.management.commands.stock_service import adicionar_acao_completa, atualizar_acoes_completas, salvar_historico_acao
from tela_cadastro.models import Worker




QUEUE_COTACOES = "fila_cotacoes"  
EXCHANGE_ELECTION = "election"     

class Command(BaseCommand):
    help = "Inicia o worker de processamento de cotações"

    def handle(self, *args, **options):
        hostname = socket.gethostname()
        pid = os.getpid()

        with transaction.atomic():
            worker = Worker.objects.create(
                hostname=hostname,
                pid=pid,
                is_leader=False,
                uptime_segundos=0,
            )

        self.stdout.write(self.style.SUCCESS(f"Worker registrado: {worker}"))

        config = RabbitMQConfig()
        connection = config.get_connection()
        channel = connection.channel()
        config.setup_exchanges_and_queues(channel)

        channel.basic_qos(prefetch_count=1)

        inicio = time.time()
        ultimo_heartbeat = 0
        INTERVALO_HEARTBEAT = 5  

        def enviar_heartbeat(force=False):
            nonlocal ultimo_heartbeat

            agora = time.time()
            if not force and (agora - ultimo_heartbeat) < INTERVALO_HEARTBEAT:
                return

            ultimo_heartbeat = agora

            uptime = int(agora - inicio)
            worker.uptime_segundos = uptime
            worker.last_heartbeat = timezone.now()
            worker.save(update_fields=["uptime_segundos", "last_heartbeat"])

            payload = {
                "worker_id": str(worker.id),
                "hostname": worker.hostname,
                "pid": worker.pid,
                "uptime": uptime,
                "timestamp": timezone.now().isoformat(),
            }

            channel.basic_publish(
                exchange=EXCHANGE_ELECTION,
                routing_key="",
                body=json.dumps(payload),
            )

        def on_message(ch, method, properties, body):
            enviar_heartbeat(force=True)

            try:
                msg = json.loads(body)
            except json.JSONDecodeError:
                print("[!] Mensagem inválida (JSON):", body)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            tipo = msg.get("type")
            print(f"[x] Recebida mensagem: type={tipo} body={msg}")

            try:
                if tipo == "atualizar_todas_acoes":
                    result = atualizar_acoes_completas()

                elif tipo == "atualizar_acao":
                    ticker = (msg.get("ticker") or "").strip().upper()
                    if not ticker:
                        result = {"ok": False, "erro": "ticker vazio na mensagem"}
                    else:
                        result = adicionar_acao_completa(ticker)

                elif tipo == "historico_acao":
                    ticker = (msg.get("ticker") or "").strip().upper()
                    periodo = msg.get("periodo", "1mo")
                    if not ticker:
                        result = {"ok": False, "erro": "ticker vazio na mensagem"}
                    else:
                        result = salvar_historico_acao(ticker, periodo)

                else:
                    result = {"ok": False, "erro": f"tipo desconhecido: {tipo}"}

                print(f"[✓] Resultado processamento: {result}")
                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                print("[!] Erro ao processar mensagem:", e)
                ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(
            queue=QUEUE_COTACOES,
            on_message_callback=on_message,
        )

        self.stdout.write(self.style.SUCCESS("Worker de cotações iniciado. Aguardando mensagens..."))

        try:
            while True:
                connection.process_data_events(time_limit=1)
                enviar_heartbeat()

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Worker finalizado manualmente (Ctrl+C)."))
        finally:
            try:
                connection.close()
            except Exception:
                pass
