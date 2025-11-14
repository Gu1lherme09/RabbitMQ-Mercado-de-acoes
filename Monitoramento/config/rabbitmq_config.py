import pika
import ssl
import os 
import time
from urllib.parse import urlparse 
from dotenv import load_dotenv

load_dotenv()

class RabbitMQConfig:
    
    def __init__(self):
        self.cloudamqp_url = os.getenv("CLOUDAMQP_URL")
        
        if self.cloudamqp_url:
            print("Usando RabbitMQ CloudAMQP")
            self._parse_cloudamqp_url()
        else:
            print("Utilizando o RabbitMQ local.")
            self.host = os.getenv("RABBITMQ_HOST", "localhost")
            self.port = int(os.getenv("RABBITMQ_PORT", 5672))
            self.username = os.getenv("RABBITMQ_USERNAME", "guest")
            self.password = os.getenv("RABBITMQ_PASSWORD", "guest")
            self.vhost = os.getenv("RABBITMQ_VHOST", "/")
            self.use_ssl = False
                    
    def _parse_cloudamqp_url(self):           
        parsed_url = urlparse(self.cloudamqp_url)
        
        self.host = parsed_url.hostname
        self.port = parsed_url.port or (5671 if parsed_url.scheme == 'amqps' else 5672)
        self.username = parsed_url.username
        self.password = parsed_url.password
        self.vhost = parsed_url.path[1:] if parsed_url.path else '/'
        self.use_ssl = parsed_url.scheme == 'amqps'
        
        print(f"RabbitMQ Config - Host: {self.host}")
        print(f"Port: {self.port}")
        print(f"VHost: {self.vhost}")
        print(f"SSL: {self.use_ssl}")
        
    def get_connection(self): 
        credentials = pika.PlainCredentials(self.username, self.password)
        
        ssl_options = None
        if self.use_ssl:
            ssl_options = pika.SSLOptions(
                context=ssl.create_default_context(), 
                server_hostname=self.host         
            )
                
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host=self.vhost,
            credentials=credentials,
            ssl_options=ssl_options,
            heartbeat=600,
            blocked_connection_timeout=300
        )        
        
        max_retries = 3
        for attempt in range(max_retries):
            try: 
                connection = pika.BlockingConnection(parameters)
                print("Conexão com RabbitMQ estabelecida com sucesso.")
                return connection
            except Exception as e: 
                print(f"Tentativa {attempt + 1}/{max_retries} falhou: {e}")
                if attempt == max_retries - 1:
                    raise 
                time.sleep(5)














