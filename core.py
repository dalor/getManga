from dtelbot import Bot
from manga_parser import MangaParser
import os

try:
    from config import *
except ImportError:
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
    await mp.send_mangalib(a.chat_id, a.args[1], a.session)

@b.callback_query('d mangalib (.+)')
async def download_mangalib(a):
    #await a.answer(text='Dont`t do it').send()
    await mp.load_all_chapters_from_mangalib(a.data['message'], a.args[1], a.session)

@b.callback_query('vls mangalib (.+) ([0-9]+) ([\<\-\>]+)')
async def download_mangalib(a):
    await mp.volumes_mangalib(a.chat_id, a.message_id, a.args[1], int(a.args[2]), a.args[3], a.session)

@b.callback_query('page ([0-9]+) ([0-9]+)')
async def page_info(a):
    page = int(a.args[1])
    per_page = int(a.args[2])
    await a.answer(text='Page {}: {} - {}'.format(page + 1, page * per_page, page * per_page + per_page - 1)).send()

@b.callback_query('main mangalib (.+)')
async def main_mangalib(a):
    await mp.back_to_main('mangalib', a.args[1], a.chat_id, a.message_id)

@b.message(True, path=['document'])
async def document(a):
    token = a.data.get('caption')
    if token:
        await mp.send_file_by_token(a.data['document']['file_id'], token)