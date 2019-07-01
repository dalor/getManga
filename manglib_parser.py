import requests
import lxml.html
import re
import asyncio
import aiohttp
import json
from base64 import b64decode

find_window_info = re.compile(r'window\.\_\_info\ \=\ ([^;]+)[\S\s]+class\=\"pp\"\>\<\!\-\-\ *([^ ]+)')
img_server = {'main':'img2','secondary':'img2','compress':'img3'} # Was loaded from https://mangalib.me/js/main.js as '{key:"server",get:function(){return{main:"img2",secondary:"img2",compress:"img3"}'

class MangaLibChapter:
    def __init__(self, url, title=None, text=None):
        self.url = url
        self.title = title
        self.text = text
        self.info = None
        self.pictures = []
    
    def __load_pictures(self):
        for page in sorted(self.info['pages'], key=lambda p: p['p']):
            self.pictures.append('https://{}.mangalib.me{}{}'.format(img_server[self.info['imgServer']], self.info['imgUrl'], page['u']))

    async def load__(self, session):
        async with session.get(self.url) as resp:
            if resp.status == 200:
                find = find_window_info.search(await resp.text())
                if find:
                    self.info = json.loads(find[1])
                    self.info['pages'] = json.loads(b64decode(find[2]))
                    self.__load_pictures()

def load_chapter(slug, v, c):
    chapter = MangaLibChapter('https://mangalib.me/{}/v{}/c{}'.format(slug, v, c))
    async def load_one():
        async with aiohttp.ClientSession() as session:
            while chapter.info:
                await chapter.load__(session)
    asyncio.new_event_loop().run_until_complete(load_one())
    return chapter

class MangaLibBook:
    def __init__(self, slug):
        self.book_url = 'https://mangalib.me/' + slug
        self.__load_chapters()
        self._info = None

    def __parse_chapter_info(self, chapter):
        chap = chapter.xpath('a')[0]
        return MangaLibChapter(chap.attrib['href'], chap.attrib['title'], chap.text.split('\n')[0])

    def __load_chapters(self):
        html = lxml.html.fromstring(requests.get(self.book_url).content)
        self.id = html.xpath('//div[@id = "comments"]')[0].attrib['data-post-id']
        self.chapters = [self.__parse_chapter_info(chapter) for chapter in html.xpath('//div[@class = "chapter-item__name"]')]
        self.chapters.reverse()

    @property
    def info(self):
        if not self._info:
            self._info = requests.get('https://mangalib.me/manga-short-info', params={'id': self.id}).json()
        return self._info

    @property
    def pictures(self):
        pics = []
        for chapter in self.chapters:
            pics.extend(chapter.pictures)
        return pics

    def load(self, lasts_callback=None):
        async def load_unloaded_chapters(session):
            to_load = [asyncio.ensure_future(one.load__(session)) for one in self.chapters if not one.info]
            if lasts_callback:
                lasts_callback(len(to_load))
            if to_load:
                await asyncio.gather(*to_load)
                return True
        async def load_all():
            async with aiohttp.ClientSession() as session:
                while await load_unloaded_chapters(session):
                    pass
        asyncio.new_event_loop().run_until_complete(load_all())
        return self.pictures

