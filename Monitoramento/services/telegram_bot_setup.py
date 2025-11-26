import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /start que retorna o chat_id do usuário.
    
    O usuário envia /start e recebe seu chat_id formatado.
    """
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    mensagem = (
        f"👋 *Olá, {user.first_name}!*\n\n"
        f"🆔 *Seu Chat ID é:*\n"
        f"`{chat_id}`\n\n"
        f"📋 *Como configurar no BolsaView:*\n"
        f"1️⃣ Copie o código acima (toque nele)\n"
        f"2️⃣ Acesse: http://localhost:8000/perfil\n"
        f"3️⃣ Cole no campo 'Chat ID'\n"
        f"4️⃣ Clique em Salvar\n\n"
        f"✅ *Pronto!* Você receberá alertas de ações aqui.\n\n"
        f"💡 *Dica:* Configure alertas em 'Selecionar Ações'"
    )
    
    await update.message.reply_text(mensagem, parse_mode='Markdown')
    
    print(f"✅ Chat ID enviado para {user.first_name} (ID: {chat_id})")


async def main():
    """Inicia o bot"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("❌ ERRO: TELEGRAM_BOT_TOKEN não encontrado no .env")
        print("Configure o token no arquivo .env primeiro!")
        return
    
    print("\n" + "="*60)
    print("🤖 BOT DE CAPTURA DE CHAT_ID")
    print("="*60)
    
    # Criar aplicação
    app = Application.builder().token(token).build()
    
    # Adicionar handler para /start
    app.add_handler(CommandHandler("start", start))
    
    # Iniciar bot
    print("\n✅ Bot rodando!")
    print("📱 Peça para os usuários enviarem /start no Telegram")
    print("🆔 Eles receberão o chat_id automaticamente\n")
    print("Pressione Ctrl+C para parar\n")
    
    # Usar initialize + start + polling ao invés de run_polling
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    try:
        # Manter o bot rodando
        import signal
        stop = asyncio.Event()
        
        def signal_handler(signum, frame):
            stop.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        await stop.wait()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == '__main__':
    asyncio.run(main())