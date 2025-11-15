import os 
import psycopg
from psycopg.rows import dict_row

class Database:
    
    def __init__(self): 
        self.db_host = os.getenv('DB_HOST')
        self.db_port = int(os.getenv('DB_PORT'))
        self.db_name = os.getenv('DB_NAME')
        self.db_user = os.getenv('DB_USER')
        self.db_pass = os.getenv('DB_PASS')
        
        
        self.conn_string = (
            f"host={self.db_host} "
            f"port={self.db_port} "
            f"dbname={self.db_name} "
            f"user={self.db_user} "
            f"password={self.db_pass}"
        )
        
        self.connection = None
        
    def connect(self):
        try: 
            self.connection = psycopg.connect(
                self.conn_string, 
                row_factory=dict_row
            )
            self.connection.autocommit = True
            print("Conexão com o banco de dados estabelecida com sucesso.")
            return self.connection
        except Exception as e:
            print(f"Falha ao conectar ao banco de dados: {e}")
            raise
    
    def execute_query(self, query, params=None):
        if not self.connection: 
            self.connect()
            
        try: 
           with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchall()
        except Exception as e:
            print(f"Erro ao executar query: {e}")
            raise
    
    def execute_update(self, query, params=None):
        if not self.connection: 
            self.connect()
            
        try: 
           with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.rowcount
        except Exception as e:
            print(f"Erro ao executar update: {e}")
            raise
        
    def close(self):
        if self.connection:
            self.connection.close()
            print("Conexão com o banco de dados fechada.")    
            
    # funções workers       
            
def register_worker(db, nome, host='localhost', port=None):
        query = """
            insert into worker (nome, host, porta, status, ultimo_heartbeat) 
            values(%s, %s, %s, 'online', CURRENT_TIMESTAMP)
            on conflict (nome) 
            do update set
                status = 'online',
                ultimo_heartbeat = CURRENT_TIMESTAMP
            RETURNING id;
            """        
        result = db.execute_query(query, (nome, host, port))    
        return result[0]['id'] if result else None
    
    
def update_worker_heartbeat(db, nome, tempo_atividade):
        query = """
            update worker 
            set ultimo_heartbeat = CURRENT_TIMESTAMP,
                tempo_atividade = %s
            where nome = %s;
            """        
        db.execute_update(query, (tempo_atividade, nome))
        
        return db.execute_update(query, (tempo_atividade, nome))
    
def set_worker_lider(db, nome):
        db.execute_update("UPDATE worker SET is_lider = FALSE")
        query = """
            update worker 
            set is_lider = TRUE where nome = %s;
            """        
        return db.execute_update(query, (nome,))
    
def get_all_workers(db):
        query = "SELECT * FROM worker order by nome"
        return db.execute_query(query)
    
    # funções ação
    
def insert_acao(db, abreviacao, nome, valor_atual):
        query = """
            insert into acao (abreviacao, nome, moeda, valor_atual, atualizado_em)
            values (%s, %s, 'BRL', %s, CURRENT_TIMESTAMP)
            on conflict (abreviacao)
            do update set
                valor_atual = EXCLUDED.valor_atual,
                atualizado_em = CURRENT_TIMESTAMP                
            RETURNING id    
            """
        result = db.execute_query(query, (abreviacao, nome, valor_atual))
        return result[0]['id'] if result else None
    
def get_acao(db, abreviacao):
        query = "SELECT * FROM acao WHERE abreviacao = %s"
        result = db.execute_query(query, (abreviacao,))
        return result[0] if result else None
    
    
    
            
            
            
                
                