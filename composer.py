import asyncio
import aiohttp
from PIL import Image
from io import BytesIO
import img2pdf

class CounterWithCallback:
    def __init__(self, callback, delta=10):
        self.i = 0
        self.callback = callback
        self.delta = delta

    async def plus(self):
        self.i += 1
        if not self.i % self.delta:
            await self.callback(self.i)

class Composer:
    def __init__(self, max_width=1024):
        self.max_width = max_width

    def create_pil(self, bytes_):
        return Image.open(BytesIO(bytes_))

    def load_pictures(self, urls, lasts_callback, delta_count):
        async def fetch_pic(session, url, cnc):
            async with session.get(url) as resp:
                if cnc:
                    await cnc.plus()
                if resp.status == 200:
                    return self.create_pil(await resp.read())
                else:
                    print(resp.status, url)
        cnc = CounterWithCallback(lasts_callback, delta_count) if lasts_callback else None
        async def load_urls():
            async with aiohttp.ClientSession() as session:
                return await asyncio.gather(*[asyncio.ensure_future(fetch_pic(session, url, cnc)) for url in urls])
        return [pic for pic in asyncio.new_event_loop().run_until_complete(load_urls()) if pic]

    def optimize_pictures(self, pictures):
        ######
        return pictures
    
    def picture_to_bytes(self, pic):
        buffer = BytesIO()
        new_img = pic.convert('RGB')
        new_img.save(buffer, format='JPEG')
        return buffer.getvalue()
    
    def pictures_to_bytes(self, pictures):
        return [self.picture_to_bytes(pic) for pic in pictures]
        
    def urls2pdf(self, urls, lasts_callback=None, delta_count=10):
        return img2pdf.convert(self.pictures_to_bytes(self.optimize_pictures(self.load_pictures(urls, lasts_callback, delta_count))))
