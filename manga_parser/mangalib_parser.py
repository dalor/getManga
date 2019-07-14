import lxml.html
import re
import asyncio
import aiohttp
import json
from base64 import b64decode
from .picture import Picture
import os

find_window_info = re.compile(r'window\.\_\_info\ \=\ ([^;]+)[\S\s]+class\=\"pp\"\>\<\!\-\-\ *([^ ]+)')
chapter_volume_with_id = re.compile(r'\/v([^\/]+)\/c([^\/]+)')
img_server = {'main':'img2','secondary':'img2','compress':'img3'} # Was loaded from https://mangalib.me/js/main.js as '{key:"server",get:function(){return{main:"img2",secondary:"img2",compress:"img3"}'

pictures_path = 'mangalib/pictures'

try:
    os.mkdir(pictures_path)
except:
    print('Folder for mangalib pictures is already existed')

class MangaLibChapter:
    def __init__(self, url, title=None, text=None):
        self.url = url
        self.title = title
        self.text = text
        self.info = None
        self.id = None
        self.pictures = []
        self.type = 'chapter'
        self.choosen = False
    
    def __load_pictures(self):
        for page in sorted(self.info['pages'], key=lambda p: p['p']):
            self.pictures.append(Picture('https://{}.mangalib.me{}{}'.format(img_server[self.info['imgServer']], self.info['imgUrl'], page['u']), (self.info['imgUrl'][1:] + page['u']).replace('/', '_'), pictures_path))

    @property
    def loaded(self):
        return True if self.info else False

    async def load(self, session):
        async with session.get(self.url) as resp:
            if resp.status == 200:
                find = find_window_info.search(await resp.text())
                if find:
                    self.info = json.loads(find[1])
                    self.info['pages'] = json.loads(b64decode(find[2]))
                    self.__load_pictures()

class MangaLibVolume:
    def __init__(self, id):
        self.id = id
        self.chapters = []
        self.choosen = True
        self.type = 'volume'

    def add(self, chapter):
        self.chapters.append(chapter)

async def load_chapter(slug, v, c, anyway=True):
    chapter = MangaLibChapter('https://mangalib.me/{}/v{}/c{}'.format(slug, v, c))
    async with aiohttp.ClientSession() as session:
        while True:
            await chapter.load(session)
            if chapter.info and anyway:
                break
    return chapter if chapter.loaded else None

class MangaLibBook:
    def __init__(self, slug):
        self.book_url = 'https://mangalib.me/' + slug
        self.slug = slug
        self._info = None
        self.id = None
        self._chapters = []
        self._volumes = {}
        self.lang = '🇷🇺'

    def __parse_chapter_info(self, chapter):
        chap = chapter.xpath('a')[0]
        url = chap.attrib['href']
        chapter = MangaLibChapter(url, chap.attrib['title'], chap.text.split('\n')[0])
        parsed_url = chapter_volume_with_id.search(url)
        if parsed_url:
            chapter.id = parsed_url[2]
            volume_id = parsed_url[1]
            volume = self._volumes.get(volume_id)
            if not volume:
                volume = MangaLibVolume(volume_id)
                self._volumes[volume_id] = volume
            volume.add(chapter)
        return chapter
            
    async def load(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.book_url) as resp:
                if (resp.status == 200):
                    self.html = lxml.html.fromstring(await resp.read())
                    self.id = self.html.xpath('//div[@id = "comments"]')[0].attrib['data-post-id']
                    self.thumbnail = self.html.xpath('//img[@class = "manga__cover"]')[0].attrib['src']
                    return self

    @property
    def chapters(self):
        if not self._chapters:
            self._chapters = [self.__parse_chapter_info(chapter) for chapter in reversed(self.html.xpath('//div[@class = "chapter-item__name"]'))]
        return self._chapters
    
    @property
    def volumes(self):
        if not self._volumes:
            self.chapters
        return self._volumes

    @property
    def volumes_list(self):
        return [val for key, val in self.volumes.items()]

    @property
    def loaded(self):
        return True if self.id else False

    @property
    async def info(self):
        if not self._info:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://mangalib.me/manga-short-info', params={'id': self.id}) as resp:
                    if resp.status == 200:
                        self._info = await resp.json()
        return self._info

    @property
    def pictures(self):
        pics = []
        for chapter in self.chapters:
            pics.extend(chapter.pictures)
        return pics

    async def load_chapters(self, lasts_callback=None):
        if not self.loaded:
            await self.load()
        async def load_unloaded_chapters(session):
            to_load = [asyncio.ensure_future(one.load(session)) for one in self.chapters if not one.info]
            if lasts_callback:
                await lasts_callback(len(to_load))
            if to_load:
                await asyncio.gather(*to_load)
                return True
        async def load_all():
            async with aiohttp.ClientSession() as session:
                while await load_unloaded_chapters(session):
                    pass
        await load_all()
        return self.pictures

