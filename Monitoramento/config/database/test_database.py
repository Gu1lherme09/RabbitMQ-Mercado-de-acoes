import sys
import os

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from dotenv import load_dotenv
load_dotenv()

from database import (
    Database,
    register_worker,
    update_worker_heartbeat,
    set_worker_lider,
    get_all_workers,
    insert_acao,
    get_acao
)


def test_connection():
    """Teste 1: Conexão básica"""
    print("\n" + "="*60)
    print("🧪 TESTE 1: Conexão com PostgreSQL")
    print("="*60)
    
    try:
        db = Database()
        db.connect()
        db.close()
        print("✅ PASSOU!\n")
        return True
    except Exception as e:
        print(f"❌ FALHOU: {e}\n")
        return False


def test_workers():
    """Teste 2: Operações com workers"""
    print("="*60)
    print("🧪 TESTE 2: Workers")
    print("="*60)
    
    try:
        db = Database()
        db.connect()
        
        # Registrar workers
        print("\n📝 Registrando workers...")
        register_worker(db, 'worker_1', 'localhost', 5000)
        register_worker(db, 'worker_2', 'localhost', 5001)
        register_worker(db, 'worker_3', 'localhost', 5002)
        print("   ✓ 3 workers registrados")
        
        # Atualizar heartbeat
        print("\n💓 Atualizando heartbeat...")
        update_worker_heartbeat(db, 'worker_1', 120)
        print("   ✓ Worker_1 heartbeat atualizado (120s)")
        
        # Definir líder
        print("\n👑 Definindo líder...")
        set_worker_lider(db, 'worker_2')
        print("   ✓ Worker_2 é o novo líder")
        
        # Listar todos
        print("\n📋 Listando workers:")
        workers = get_all_workers(db)
        for w in workers:
            lider = "👑" if w['is_lider'] else "  "
            print(f"   {lider} {w['nome']} - {w['status']} - {w['tempo_atividade']}s")
        
        db.close()
        print("\n✅ PASSOU!\n")
        return True
        
    except Exception as e:
        print(f"❌ FALHOU: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_acoes():
    """Teste 3: Operações com ações"""
    print("="*60)
    print("🧪 TESTE 3: Ações")
    print("="*60)
    
    try:
        db = Database()
        db.connect()
        
        # Inserir ação
        print("\n📝 Inserindo ação PETR4...")
        insert_acao(db, 'PETR4', 'Petrobras', 28.50)
        print("   ✓ Inserido")
        
        # Buscar ação
        print("\n🔍 Buscando ação PETR4...")
        acao = get_acao(db, 'PETR4')
        print(f"   ✓ Encontrado: {acao['nome']} - R$ {acao['valor_atual']}")
        
        # Atualizar ação
        print("\n📝 Atualizando ação PETR4...")
        insert_acao(db, 'PETR4', 'Petrobras', 28.75)
        acao = get_acao(db, 'PETR4')
        print(f"   ✓ Atualizado: R$ {acao['valor_atual']}")
        
        db.close()
        print("\n✅ PASSOU!\n")
        return True
        
    except Exception as e:
        print(f"❌ FALHOU: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Executa todos os testes"""
    print("\n" + "🚀"*30)
    print("TESTE COMPLETO - POSTGRESQL")
    print("🚀"*30)
    
    test1 = test_connection()
    test2 = test_workers()
    test3 = test_acoes()
    
    print("\n" + "="*60)
    print("📊 RESULTADO FINAL")
    print("="*60)
    print(f"Teste 1 (Conexão): {'✅ PASSOU' if test1 else '❌ FALHOU'}")
    print(f"Teste 2 (Workers): {'✅ PASSOU' if test2 else '❌ FALHOU'}")
    print(f"Teste 3 (Ações):   {'✅ PASSOU' if test3 else '❌ FALHOU'}")
    print("="*60)
    
    if test1 and test2 and test3:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("\n✨ PostgreSQL funcionando perfeitamente!\n")
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM\n")


if __name__ == "__main__":
    main()