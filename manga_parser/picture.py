from PIL import Image
from io import BytesIO
import os.path
import os
from threading import Thread
import urllib3

urllib3.disable_warnings()

http = urllib3.PoolManager()

class Picture(Thread):
    def __init__(self, url, filepath, base_dir=''):
        Thread.__init__(self)
        self.url = url
        self.loaded = False
        self.cnc = None
        self.filepath = os.path.join(base_dir, filepath)
        self.change_filename_extension()

    def change_filename_extension(self):
        ext = self.filepath.split('.')[-1]
        self.filepath = self.filepath.replace('.' + ext, '.jpg')

    def download(self, cnc=None):
        if cnc:
            self.cnc = cnc
        self.start()

    def optimize(self, img):
        ### Optimize size
        return img

    def run(self):
        resp = http.request('GET', self.url, preload_content=False)
        if resp.status == 200:
            self.optimize(Image.open(resp)).convert('RGB').save(self.filepath, 'JPEG')
            self.loaded = True
            if self.cnc:
                self.cnc.plus()
        else:
            print(resp.status, self.url)
        resp.release_conn()