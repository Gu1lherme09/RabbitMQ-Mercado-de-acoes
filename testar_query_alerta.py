import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Consultor_bolsa.settings')
django.setup()

from django.db import connection

# Testar a query do alerta_service
print("="*60)
print("TESTANDO QUERY DO ALERTA_SERVICE:")
print("="*60)

cursor = connection.cursor()

# Query ERRADA (atual)
try:
    cursor.execute("""
        SELECT 
           m.id as alerta_id,
           'preco' as tipo_alerta,
            CASE 
                WHEN m.direcao = 'acima' THEN '>'
                WHEN m.direcao = 'acima_ou_igual' THEN '>='
                WHEN m.direcao = 'abaixo' THEN '<'
                WHEN m.direcao = 'abaixo_ou_igual' THEN '<='
            END as operador,
            m.preco_alvo as valor_referencia,
            u.id as usuario_id,
            u.email,
            u.chat_id,
            a.id as acao_id,
            a.abreviacao,
            a.nome as acao_nome,
            a.valor_atual,
            FALSE as disparado  
        FROM monitoramento m
        INNER JOIN usuario u ON m.usuario_id = u.id
        INNER JOIN acao a ON m.acao_id = a.id
        WHERE m.ativo = TRUE
    """)
    
    results = cursor.fetchall()
    print(f"\n❌ Query ERRADA retornou {len(results)} resultados")
    
except Exception as e:
    print(f"\n❌ Query ERRADA falhou: {e}")

# Query CORRETA (com nomes reais das tabelas)
try:
    cursor.execute("""
        SELECT 
           m.id as alerta_id,
           'preco' as tipo_alerta,
            CASE 
                WHEN m.direcao = 'acima' THEN '>'
                WHEN m.direcao = 'acima_ou_igual' THEN '>='
                WHEN m.direcao = 'abaixo' THEN '<'
                WHEN m.direcao = 'abaixo_ou_igual' THEN '<='
            END as operador,
            m.preco_alvo as valor_referencia,
            u.id as usuario_id,
            u.email,
            u.chat_id,
            a.id as acao_id,
            a.abreviacao,
            a.nome as acao_nome,
            a.valor_atual,
            FALSE as disparado  
        FROM tela_cadastro_monitoramento m
        INNER JOIN tela_cadastro_usuario u ON m.usuario_id = u.id
        INNER JOIN tela_cadastro_acao a ON m.acao_id = a.id
        WHERE m.ativo = TRUE
    """)
    
    results = cursor.fetchall()
    print(f"\n✅ Query CORRETA retornou {len(results)} resultados")
    
    if results:
        print("\nAlertas encontrados:")
        for row in results:
            print(f"\n  Alerta ID: {row[0]}")
            print(f"  Usuário: {row[4]} (ID: {row[3]})")
            print(f"  Chat ID: {row[5]}")
            print(f"  Ação: {row[7]} - {row[8]}")
            print(f"  Valor Atual: R$ {row[9]}")
            print(f"  Condição: {row[2]} R$ {row[10]}")
            
except Exception as e:
    print(f"\n❌ Query CORRETA falhou: {e}")

cursor.close()

print("\n" + "="*60)
print("CONCLUSÃO:")
print("="*60)
print("Os nomes corretos das tabelas são:")
print("  - tela_cadastro_monitoramento (não 'monitoramento')")
print("  - tela_cadastro_usuario (não 'usuario')")
print("  - tela_cadastro_acao (não 'acao')")
