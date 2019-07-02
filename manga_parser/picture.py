from PIL import Image
from io import BytesIO

class Picture:
    def __init__(self, url):
        self.url = url
        self.data = None

    @property
    def loaded(self):
        return True if self.data else False

    def to_PIL(self, bytes_):
        self.data = Image.open(BytesIO(bytes_))

    async def load(self, session, cnc=None):
        print(self.url)
        async with session.get(self.url) as resp:
            if resp.status == 200:
                try: #
                    self.to_PIL(await resp.read())
                    if cnc:
                        await cnc.plus()
                except: #
                    pass #
            else:
                print('Error: {}: {}'.format(resp.status, self.url))
            return self
    
    def to_bytes(self):
        if self.data:
            buffer = BytesIO()
            self.data = self.data.convert('RGB')
            self.data.save(buffer, format='JPEG')
            return buffer.getvalue()