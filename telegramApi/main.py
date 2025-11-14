import telebot

API_TOKEN ="8152587420:AAFzmohx1ZGJMVgFjPUlypCB4j0YNx1wWpk"

bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=["start"])
def enviar_ola(message):
    mensagem = """Olá! Bem-vindo! 
É neste canal que você vai receber as notificações sobre suas ações monitoradas.

Comandos disponíveis:
/start - Mensagem de boas-vindas
/help - Ajuda sobre como usar o bot"""
    
    bot.reply_to(message, mensagem)

@bot.message_handler(commands=["help"])
def enviar_ajuda(message):
    ajuda = """🤖 *Bot de Monitoramento de Ações*

Este bot enviará notificações quando suas ações atingirem os preços alvos configurados.

*Comandos:*
/start - Iniciar o bot
/help - Mostrar esta mensagem de ajuda
/configurar - Configurar monitoramento de ações

Para configurar o monitoramento de ações, acesse o sistema web."""
    
    bot.reply_to(message, ajuda, parse_mode='Markdown')

if __name__ == "__main__":
    print("🤖 Bot do Telegram iniciado...")
    print(f"Bot ID: @{bot.get_me().username}")
    bot.infinity_polling()

