import asyncio
import aiohttp
import img2pdf
import os.path
from .downloader import Downloader

class CounterWithCallback:
    def __init__(self, callback, delta=10):
        self.i = 0
        self.callback = callback
        self.delta = delta

    def plus(self):
        self.i += 1
        if not self.i % self.delta:
            self.callback(self.i)

    def end(self, last):
        self.callback(last)

class Composer:
    def __init__(self, delta_count=10, pack_size=1000):
        self.delta_count = delta_count
        self.pack_size = pack_size
        self.timesleep = 2
        self.downloader = Downloader()
        self.downloader.start()

    async def load_pictures(self, pics, lasts_callback):
        cnc = CounterWithCallback(lasts_callback, self.delta_count) if lasts_callback else None
        for pic in pics:
            pic.cnc = cnc
        self.downloader.add(pics)
        not_downloaded = True
        while not_downloaded:
            not_downloaded = False
            for pic in pics:
                if not pic.loaded:
                    not_downloaded = True
                    break
            await asyncio.sleep(self.timesleep)
        filenames = [pic.filepath for pic in pics]
        cnc.end(len(filenames))
        return filenames
               
    async def pics2pdf(self, pics, filename, lasts_callback=None, base_dir=''):
        pictures = await self.load_pictures(pics, lasts_callback)
        with open(os.path.join(base_dir, filename), 'wb') as f:
            img2pdf.convert(pictures, outputstream=f)
