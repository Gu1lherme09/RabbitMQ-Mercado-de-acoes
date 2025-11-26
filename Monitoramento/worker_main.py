# worker_main.py (na pasta monitoramento/)
"""
Script para iniciar um worker.

Uso: python worker_main.py worker_1
"""

import sys
import os
from dotenv import load_dotenv
from models.worker import Worker


# Carregar .env
load_dotenv()




def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python worker_main.py <worker_id>")
        print("Exemplo: python worker_main.py worker_1")
        sys.exit(1)
    
    worker_id = sys.argv[1]
    
    print(f"\n🚀 Iniciando {worker_id}...\n")
    
    workers = Worker(worker_id)
    workers.start()


if __name__ == "__main__":
    main()