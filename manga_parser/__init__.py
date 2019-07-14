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
        self.bot_name = None
        self.callback_timesleep = 2
        self.per_page = 10
        self.files = {}
        self.nav_codes = lambda c: 10**(len(c)-1) if c[0] == '>' else -10**(len(c)-1) if c[0] == '<' else  0

    async def set_bot_name(self):
        result = await (self.bot.getme().send())
        self.bot_name = '@' + result['result']['username']

    def navbar(self, count, nav_text, buttons=[]):
        if count > 10:
            buttons = [button('<', callback_data='{} <'.format(nav_text))] + buttons + [button('>', callback_data='{} >'.format(nav_text))]
        if count > 100:
            buttons = [button('<<', callback_data='{} <<'.format(nav_text))] + buttons + [button('>>', callback_data='{} >>'.format(nav_text))]
        if count > 1000:
            buttons = [button('<<<', callback_data='{} <<<'.format(nav_text))] + buttons + [button('>>>', callback_data='{} >>>'.format(nav_text))]
        return buttons

    def main_menu(self, source, id):
        return [
                [button('Volumes', callback_data='vls {} {} 0 -'.format(source, id))],
                [button('Download', callback_data='d {} {}'.format(source, id))]
            ]

    async def load_mangalib_book(self, session, id, new=False):
        from_session = session.get('mangalib')
        if from_session is None:
            from_session = {}
            session['mangalib'] = from_session
        book = from_session.get(id) if not new else None
        if not book:
            book = await MangaLibBook(id).load()
            if book:
                from_session[id] = book
        return book if book.loaded else None


    async def send_manga(self, chat_id, source, id, thumbnail, name, other_name, lang, description, chapters, volumes):
        await self.bot.photo(thumbnail, chat_id=chat_id, caption='<b>{}\n{}[{}]</b>\n{}\nVolumes: <code>{}</code>\nChapters: <code>{}</code>'.format(name, other_name, lang, description, len(volumes), len(chapters)),
             parse_mode='HTML', reply_markup=markup(self.main_menu(source, id))).send()

    async def send_mangalib(self, chat_id, id, session):
        book = await self.load_mangalib_book(session, id, True)
        if book:
            info = await book.info
            await self.send_manga(chat_id, 'mangalib', id, book.thumbnail, info['name'], info['rus_name'], book.lang, info['summary'].replace('<br>', ''), book.chapters, book.volumes)

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
        callback_pic = Clock(status_pictures, self.callback_timesleep)
        filename = '{}_{}_{}'.format(msg.chat_id, msg.message_id, filename)
        await asyncio.gather(self.composer.pics2pdf(pictures, filename, callback_pic.set_args), callback_pic.start(lambda n: n < pic_count - 1))
        async def status_uploading(num, all_):
            await msg.next('Uploading: {} %'.format(int(num/all_*100)))
        await self.send_via_telethon(filename, msg.chat_id, status_uploading)
        await msg.next('Uploaded!!!')

    async def back_to_main(self, source, id, chat_id, message_id):
        await self.bot.editreplymarkup(chat_id=chat_id, message_id=message_id, reply_markup=markup(self.main_menu(source, id))).send()

    async def load_all_chapters_from_mangalib(self, message, id, session):
        book = await self.load_mangalib_book(session, id)
        if book:
            await self.load_all_chapters(message, book, id + '.pdf')

    async def send_via_telethon(self, file, chat_id, progress_callback):
        callback = Clock(progress_callback, self.callback_timesleep)
        token = str(random_token())
        async def send_file(telethon):
            self.set_file_to_send(token, chat_id)
            if not self.bot_name:
                await self.set_bot_name()
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

    async def content_list(self, chat_id, message_id, id, page, source, volumes, turn=None):
        lines_count = 0
        lines = []
        for vol in volumes:
            lines.append(vol)
            if vol.choosen:
                lines.extend(vol.chapters)
                lines_count += (2 + len(vol.chapters))
            else:
                lines_count += 1
        if turn:
            pages = lines_count // self.per_page + 1
            vector = self.nav_codes(turn)
            start_page = pages + page + vector if page + vector < 0 else page + vector if page + vector < pages else page + vector - pages
        else:
            start_page = page
        start = start_page * self.per_page
        end = None if start + self.per_page > lines_count else start + self.per_page
        buttons_lines = []
        for line in lines[start:end]:
            if line.type == 'chapter':
                buttons_lines.append([button('{} {}: {}'.format('✅' if line.choosen else '📑', line.id, line.title), callback_data='c{} {} {} {}'.format(0 if line.choosen else 1, source, id, line.id))])
            elif line.type == 'volume':
                buttons_lines.append([button('📁 Volume {}'.format(line.id), callback_data='v{} {} {} {}'.format(0 if line.choosen else 1, source, id, line.id))])
                if line.choosen:
                    buttons_lines.append([button('Choose all'.format(line.id), callback_data='c_all {} {} {}'.format(source, id, line.id))])
        buttons = [[button('< To main', callback_data='main mangalib {}'.format(id))]] + buttons_lines + [self.navbar(lines_count, 'vls mangalib {} {}'.format(id, start_page), [button(start_page + 1, callback_data='page {} {}'.format(start_page, self.per_page))])]
        await self.bot.editreplymarkup(chat_id=chat_id, message_id=message_id, reply_markup=markup(buttons)).send()

    async def volumes_mangalib(self, chat_id, message_id, id, page, turn, session):
        book = await self.load_mangalib_book(session, id)
        if book:
            await self.content_list(chat_id, message_id, id, page, 'mangalib', book.volumes_list, turn)

    #async def set_volume_choose(chat, i)
        
class Clock:
    def __init__(self, async_callback, delta):
        self.callback = async_callback
        self.delta = delta
        self.args = None
        self.is_running = True

    def set_args(self, *args):
        self.args = args

    async def start(self, while_=None):
        while self.is_running and not (while_ and self.args and not while_(*self.args)):
            if self.args:
                await self.callback(*self.args)
            await asyncio.sleep(self.delta)

    def stop(self):
        self.is_running = False
