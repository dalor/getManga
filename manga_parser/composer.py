import asyncio
import aiohttp
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
    def __init__(self, max_width=1024, delta_count=10, pack_size=300):
        self.max_width = max_width
        self.delta_count = delta_count
        self.pack_size = pack_size

    async def load_pictures(self, pics, lasts_callback):
        cnc = CounterWithCallback(lasts_callback, self.delta_count) if lasts_callback else None
        async def load_pictures_(pictures):
            async with aiohttp.ClientSession() as session:
                return await asyncio.gather(*[asyncio.ensure_future(pic.load(session, cnc)) for pic in pictures])
        while True:
            pics_to_load = [pic for pic in pics if not pic.loaded]
            if pics_to_load:
                for i in range(len(pics_to_load) // self.pack_size):
                    await load_pictures_(pics_to_load[i*self.pack_size:None if (i+1)*self.pack_size > len(pics_to_load) else (i+1)*self.pack_size])
            else:
                break

    def optimize_pictures(self, pictures):
        for pic in pictures:
            pass
            #pic.resize()
    
    def pictures_to_bytes(self, pictures):
        return [pic.to_bytes() for pic in pictures]
        
    async def pics2pdf(self, pics, lasts_callback=None):
        await self.load_pictures(pics, lasts_callback)
        self.optimize_pictures(pics)
        return img2pdf.convert(self.pictures_to_bytes(pics))
