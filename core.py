from dtelbot import Bot
from manga_parser import MangaParser
import os

BOT_TOKEN = os.environ['BOT_TOKEN']

API_ID = os.environ['API_ID']
API_HASH = os.environ['API_HASH']
TELETHON_SESSION = os.environ['TELETHON_SESSION']

telethon_params = (TELETHON_SESSION, API_ID, API_HASH)

b = Bot(BOT_TOKEN)

mp = MangaParser(b, telethon_params)

@b.message('/start')
async def start(a):
    await a.msg('Hello').send()

@b.message('.+/mangalib.me/([^/]+)')
async def mangalib(a):
    await mp.send_mangalib(a.chat_id, a.args[1])

@b.callback_query('d mangalib (.+)')
async def download_mangalib(a):
    await mp.load_all_chapters_from_mangalib(a.data['message'], a.args[1])

@b.message(True, path=['document'])
async def document(a):
    token = a.data.get('caption')
    if token:
        await mp.send_file_by_token(a.data['document']['file_id'], token)

if __name__ == '__main__':
    b.polling()