class StatusMessage:
    def __init__(self, bot, message, text='', **kwargs):
        self.bot = bot
        self.text = text
        self.chat_id = message['chat']['id']
        self.message_id = message['message_id']
        self.prev_text = None

    async def edit_text(self, text):
        if not text == self.prev_text:
            self.prev_text = text
            await self.bot.editcaption(text, self.chat_id, self.message_id, parse_mode='HTML').send()

    async def next(self, text):
        await self.edit_text(self.text + '\n' + text)