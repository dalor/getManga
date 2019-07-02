from .composer import Composer
from .mangalib_parser import MangaLibBook, load_chapter
from .status import StatusMessage

from uuid import uuid4 as random_token
import asyncio
from io import BytesIO

from dtelbot.inline_keyboard import markup, button
from telethon import TelegramClient
from telethon.sessions.string import StringSession

class MangaParser:
    def __init__(self, bot, telethon_params):
        self.composer = Composer()
        self.bot = bot
        self.telethon_session = telethon_params[0]
        self.telethon_api_id = telethon_params[1]
        self.telethon_api_hash = telethon_params[2]
        self.bot_name = '@GetMangaBot'
        self.callback_timesleep = 2
        self.files = {}

    async def send_manga(self, chat_id, source, id, thumbnail, name, other_name, lang, description, chapters_count):
        await self.bot.photo(thumbnail, chat_id=chat_id, caption='<b>{}\n{}[{}]</b>\n{}\nChapters: <code>{}</code>'.format(name, other_name, lang, description, chapters_count), parse_mode='HTML', reply_markup=markup([[button('Download', callback_data='d {} {}'.format(source, id))]])).send()

    async def send_mangalib(self, chat_id, id):
        book = await MangaLibBook(id).load()
        if book:
            info = await book.info
            await self.send_manga(chat_id, 'mangalib', id, book.thumbnail, info['name'], info['rus_name'], book.lang, info['summary'].replace('<br>', ''), len(book.chapters))

    async def load_all_chapters(self, message, book, filename):
        msg = StatusMessage(self.bot, message, '<i>Loading...</i>')
        chapter_count = len(book.chapters)
        await msg.next('Loading {} chapters...'.format(chapter_count))
        async def status_chapters(num):
            await msg.next('Chapters loaded: {}/{}'.format(chapter_count - num, chapter_count))
        pictures = await book.load_chapters(status_chapters)
        pic_count = len(pictures)
        await msg.next('Loading {} pictures...'.format(pic_count))
        async def status_pictures(num):
            await msg.next('Pictures loaded: {}/{}'.format(num, pic_count))
        pdf_file = BytesIO(await self.composer.pics2pdf(pictures, status_pictures))
        pdf_file.name = filename
        async def status_uploading(num, all_):
            await msg.next('Uploading: {} %'.format(int(num/all_*100)))
        await self.send_via_telethon(pdf_file, msg.chat_id, status_uploading)
        await msg.next('Uploaded!!!')

    async def load_all_chapters_from_mangalib(self, message, id):
        book = await MangaLibBook(id).load()
        if book:
            await self.load_all_chapters(message, book, id + '.pdf')

    async def send_via_telethon(self, file, chat_id, progress_callback):
        callback = Clock(progress_callback, self.callback_timesleep)
        token = str(random_token())
        async def send_file(telethon):
            self.set_file_to_send(token, chat_id)
            await telethon.send_file(self.bot_name, file, caption=token, progress_callback=callback.set_args)
            callback.stop()
        async with TelegramClient(StringSession(self.telethon_session), self.telethon_api_id, self.telethon_api_hash) as telethon:
            await asyncio.gather(send_file(telethon), callback.start())
            
    def set_file_to_send(self, token, chat_id):
        self.files[token] = {'chat_id': chat_id}

    def get_file_to_send(self, token):
        return self.files.get(token)

    async def send_file_by_token(self, file_id, token):
        unfile = self.get_file_to_send(token)
        if unfile:
            await self.bot.document(file_id, unfile['chat_id']).send()

class Clock:
    def __init__(self, async_callback, delta):
        self.callback = async_callback
        self.delta = delta
        self.args = None
        self.is_running = True

    def set_args(self, *args):
        self.args = args

    async def start(self):
        while self.is_running:
            if self.args:
                await self.callback(*self.args)
            await asyncio.sleep(self.delta)

    def stop(self):
        self.is_running = False
