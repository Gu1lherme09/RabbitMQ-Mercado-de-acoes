import pika 
import os 
import time
from urllib.parse import urlparse

class RabbitMQConfig:
    
    def __init__(self): 
        self.cloudamqp_url = os.getenv('CLOUDAMQP_URL')
        
        if  self.cloudamqp_url: 
            print("Conectando ao RabbitMQ na CloudAMQP...")
            self._parse_cloudamqp_url()
        else: 
            print("Conectando ao RabbitMQ local...")
            self.host = os.getenv('RABBITMQ_HOST')
            self.port = int(os.getenv('RABBITMQ_PORT'))
            self.username = os.getenv('RABBITMQ_USERNAME')
            self.password = os.getenv('RABBITMQ_PASSWORD')
            self.virtual_host = os.getenv('RABBITMQ_VHOST', '/')
            self.use_ssl = False
    
    def _parse_cloudamqp_url(self):
        parsed = urlparse(self.cloudamqp_url)
        self.host = parsed.hostname
        self.port = parsed.port or 5671
        self.username = parsed.username
        self.password = parsed.password
        self.vhost = parsed.path[1:]  if parsed.path else '/'
        self.use_ssl = parsed.scheme == 'amqps'
                
        print(f"   Host: {self.host}")
        print(f"   Porta: {self.port}")
        print(f"   VHost: {self.vhost}")
        print(f"   SSL: {'Ativado' if self.use_ssl else 'Desativado'}")        
        
    def get_connection(self):
        
        credentials = pika.PlainCredentials(self.username, self.password)
        
        ssl_options = None
        if self.use_ssl:
            import ssl
            ssl_options = pika.SSLOptions(
                context=ssl.create_default_context(), 
                server_hostname=self.host
            )
        
        parameters = pika.ConnectionParameters (
            host=self.host, 
            port=self.port,
            virtual_host=self.vhost,
            credentials=credentials,
            ssl_options=ssl_options, 
            heartbeat=600,          
            blocked_connection_timeout=300, 
            socket_timeout=10  
        )    
        
        
        max_retires = 3 
        for attempt in range(max_retires): 
            try: 
                print(f"Tentativa de conexão {attempt + 1} de {max_retires}...")
                connection = pika.BlockingConnection(parameters)
                print("Conexão com RabbitMQ estabelecida com sucesso.")
                return connection
            except pika.exceptions.AMQPConnectionError as e:
                print(f"Falaha: {e}")
                if attempt == max_retires - 1:
                    print("\nN�mero m�ximo de tentativas de conex�o atingido. Abortando.")
                    raise
                print("Tentando novamente em 5 segundos...\n")
                time.sleep(5)
    
    def setup_exchanges_and_queues(self, channel): 
        print("CONFIGURANDO RABBIT MQ...\n")
        
        print("Criando exchanges ...")
        
        channel.exchange_declare(
            exchange='stock_topic', 
            exchange_type='topic', 
            durable=True
        )
        
        channel.exchange_declare(
            exchange='election', 
            exchange_type='topic', 
            durable=True
        )
        
        print("\nCriando filas ...")
        
        channel.queue_declare(
            queue='fila_cotacoes', 
            durable=True, 
            arguments={
                'x-message-ttl': 60000, 
                'x-max-length': 1000     
             } 
        )
        
        print("\n fila_cotacoes criada com sucesso.")
        
        channel.queue_declare(
            queue='fila_alertas', 
            durable=True, 
            arguments={
                'x-message-ttl': 30000
             } 
        )
        
        print("\n fila_alertas criada com sucesso.")
        
        channel.queue_declare(
            queue='fila_notificacoes',
            durable=True, 
        )
        
        print("\n fila_notificacoes criada com sucesso.")
        
        
        channel.queue_declare(
            queue='fila_heartbeat',
            durable=False, 
            arguments={
                'x-message-ttl': 20000, 
                'x-max-length': 100         
            }
        )   
        
        print("\n fila_heartbeat criada com sucesso.")
                
        print("\nConfigurando bindings ...\n")
        channel.queue_bind(
            exchange='stock_topic', 
            queue='fila_cotacoes',
            routing_key='cotacao.#'
        )
        
        print(" stock_topic ? fila_cotacoes (routing: cotacao.#)")
        print("\n Binding para fila_cotacoes criado com sucesso.")
        
        
        channel.queue_bind(
            exchange='stock_topic', 
            queue='fila_alertas',
            routing_key='alerta.#'
        )
          
        print(" stock_topic ? fila_alertas (routing: alerta.#)")
        print("\n Binding para fila_alertas criado com sucesso.")
        
        channel.queue_bind(
            exchange='election', 
            queue='fila_heartbeat'
        )
        
        print(" election ? fila_heartbeat")
        print("\n Binding para fila_heartbeat criado com sucesso.")
                
        print("\nConfigura��o do RabbitMQ conclu�da com sucesso.")
        
        
    
        
        
        
        
        
        
                    
                
                
                
                
                
        