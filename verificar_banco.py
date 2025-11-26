import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Consultor_bolsa.settings')
django.setup()

from django.db import connection

# Listar todas as tabelas
cursor = connection.cursor()
cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
tables = cursor.fetchall()

print("="*60)
print("TABELAS NO BANCO:")
print("="*60)
for table in tables:
    print(f"  - {table[0]}")

# Verificar a tabela de usuários
print("\n" + "="*60)
print("VERIFICANDO DADOS DE USUÁRIOS:")
print("="*60)

from tela_cadastro.models import Usuario, Monitoramento

usuarios_count = Usuario.objects.count()
print(f"\n📊 Total de usuários: {usuarios_count}")

if usuarios_count > 0:
    print("\nUsuários cadastrados:")
    for user in Usuario.objects.all()[:5]:
        print(f"  - ID: {user.id}, Username: {user.username}, Email: {user.email}, Chat ID: {user.chat_id or 'Não configurado'}")

# Verificar monitoramentos
print("\n" + "="*60)
print("VERIFICANDO MONITORAMENTOS:")
print("="*60)

monitoramentos_count = Monitoramento.objects.count()
print(f"\n📊 Total de monitoramentos: {monitoramentos_count}")

if monitoramentos_count > 0:
    print("\nMonitoramentos ativos:")
    for mon in Monitoramento.objects.filter(ativo=True).select_related('usuario', 'acao')[:10]:
        print(f"  - {mon.usuario.username}: {mon.acao.abreviacao} {mon.direcao} R$ {mon.preco_alvo}")

# Descobrir o nome real da tabela no PostgreSQL
print("\n" + "="*60)
print("ESTRUTURA DA TABELA DE USUÁRIOS:")
print("="*60)

cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema='public' AND table_name LIKE '%user%' 
    ORDER BY table_name
""")

user_tables = cursor.fetchall()
print("\nTabelas relacionadas a usuários:")
for t in user_tables:
    print(f"  - {t[0]}")

cursor.close()
