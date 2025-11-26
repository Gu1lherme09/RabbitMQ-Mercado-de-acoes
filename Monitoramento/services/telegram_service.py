import os
import asyncio
from telegram import Bot
from telegram.error import TelegramError


class TelegramService:
    
    def __init__(self): 
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        if not self.token:
            raise ValueError("Telegram bot token não configurado no .env!")
        
        self.bot = Bot(token=self.token)
        print(f"Telegram bot inicializado")
        
    async def enviar_mensagem(self, chat_id, mensagem):
        try: 
            await self.bot.send_message(
                chat_id=chat_id,
                text=mensagem, 
                parse_mode='Markdown'
            )
            
            print(f"Mensagem enviada para chat_id {chat_id}")
            return True
        except TelegramError as e:
            print(f"Erro ao enviar mensagem para chat_id {chat_id}: {e}")
            return False
        
    async def enviar_alerta(self, chat_id, acao, preco_atual, codicao, valor_alvo): 
        mensagem = (
            f"*ALERTA DISPARADO!*\n\n"
            f"Ação: *{acao}*\n"
            f"Preço Atual: *R$ {preco_atual:.2f}*\n"
            f"Condição: *{codicao}* *R$ {valor_alvo:.2f}*"            
        )
        
        return await self.enviar_mensagem(chat_id, mensagem)
    
    async def testar_conexao(self): 
        
        try: 
            me = await self.bot.get_me()
            print(f"Conexão com Telegram OK! Bot: @{me.username}")
            return True
        except TelegramError as e:
            print(f"Erro ao conectar com Telegram: {e}")
            return False
        
def enviar_notificao_sync(chat_id, mensagem):
    service = TelegramService()
    try: 
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    return loop.run_until_complete(
        service.enviar_mensagem(chat_id, mensagem)
    )
        