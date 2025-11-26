# Monitoramento/services/test_telegram.py
"""
Testa envio de mensagem via Telegram.

IMPORTANTE: Antes de rodar, você precisa:
1. Abrir conversa com seu bot no Telegram
2. Enviar qualquer mensagem (ex: /start)
3. Pegar seu chat_id
"""

import sys
import os

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from dotenv import load_dotenv
load_dotenv()

import asyncio
from telegram_service import TelegramService


async def main():
    print("\n" + "="*60)
    print("🧪 TESTE DO TELEGRAM BOT")
    print("="*60)
    
    # Inicializar serviço
    telegram = TelegramService()
    
    # Testar conexão
    print("\n📡 Testando conexão...")
    if not await telegram.testar_conexao():
        print("❌ Falha na conexão!")
        return
    
    # Pedir chat_id
    print("\n" + "="*60)
    print("📝 COMO PEGAR SEU CHAT_ID:")
    print("="*60)
    print("1. Abra o Telegram")
    print("2. Busque seu bot (ex: @BolsaViewAlertas_bot)")
    print("3. Envie qualquer mensagem (ex: /start)")
    print("4. Acesse: https://api.telegram.org/bot<SEU_TOKEN>/getUpdates")
    print("5. Procure por 'chat':{'id': 123456789}")
    print("="*60)
    
    chat_id = input("\n✍️  Digite seu chat_id: ").strip()
    
    if not chat_id:
        print("❌ Chat ID vazio!")
        return
    
    # Enviar mensagem de teste
    print(f"\n📤 Enviando mensagem de teste para {chat_id}...")
    
    sucesso = await telegram.enviar_mensagem(
        chat_id=chat_id,
        mensagem="🎉 *Teste do BolsaView!*\n\nSe você recebeu esta mensagem, o bot está funcionando perfeitamente! ✅"
    )
    
    if sucesso:
        print("\n✅ TESTE PASSOU!")
        print("Verifique seu Telegram!")
    else:
        print("\n❌ TESTE FALHOU!")
        print("Verifique se:")
        print("- Chat ID está correto")
        print("- Você enviou mensagem para o bot primeiro")
        print("- Token está correto no .env")


if __name__ == "__main__":
    asyncio.run(main())