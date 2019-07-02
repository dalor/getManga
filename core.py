from dtelbot import Bot
from dtelbot.inline_keyboard import markup, button
from mangalib_parser import MangaLibBook, load_chapter
from composer import Composer

b = Bot('880652592:AAFxVMgpTunbkSWqGe66OiBVigDISOZHJIk')

composer = Composer()

class StatusMessage:
    def __init__(self, a, text='', **kwargs):
        self.a = a
        self.text = text
        self.chat_id = a.data['message']['chat']['id']
        self.message_id = a.data['message']['message_id']
        #self.a.bot.editreplymarkup(chat_id=self.chat_id, message_id=self.message_id).send()

    async def edit_text(self, text):
        await self.a.bot.editcaption(text, self.chat_id, self.message_id, parse_mode='HTML').asend()

    async def next(self, text):
        print(text)
        await self.edit_text(self.text + '\n' + text)

@b.message('/start')
def start(a):
    a.msg('Hello').send()

@b.message('.+/mangalib.me/([^/]+)')
def mangalib(a):
    book = MangaLibBook(a.args[1])
    if book.loaded:
        info = book.info
        a.photo(book.thumbnail, caption='<b>{}\n{}[{}]</b>\n{}\nChapters: <code>{}</code>'.format(info['name'], info['rus_name'], book.lang, info['summary'].replace('<br>', ''), len(book.chapters)), parse_mode='HTML', reply_markup=markup([[button('Download', callback_data='d mangalib {}'.format(a.args[1]))]])).send()

@b.callback_query('d mangalib (.+)')
def download_mangalib(a):
    book = MangaLibBook(a.args[1])
    if book.loaded:
        msg = StatusMessage(a, '<b>{}</b>\n<i>Loading...</i>'.format(book.info['name']))
        chapter_count = len(book.chapters)
        async def status_chapters(num):
            await msg.next('Chapters loaded: {}/{}'.format(chapter_count - num, chapter_count))
        pictures = book.load(status_chapters)
        pic_count = len(pictures)
        async def status_pictures(num):
            await msg.next('Pictures loaded: {}/{}'.format(num, pic_count))
        pdf_file = composer.urls2pdf(pictures, status_pictures)
        ### sending



if __name__ == '__main__':
    b.polling()