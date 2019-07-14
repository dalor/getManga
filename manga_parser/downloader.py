from threading import Thread
from time import sleep

class Queue:
    def __init__(self):
        self.all = []
        self.iter = -1

    def add(self, list_):
        self.all.append(list_)

    def next(self):
        if self.all:
            self.iter += 1
            if len(self.all) <= self.iter:
                self.iter = 0
            list_ = self.all[self.iter]
            if list_:
                item = list_.pop(0)
                if not list_:
                    self.all.remove(list_)
                return item

class Downloader(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.loading = []
        self.queue = Queue()
        self.max = 64

    def add(self, list_):
        self.queue.add(list_.copy())

    def run(self):
        while True:
            self.loading = [l for l in self.loading if not l.loaded]
            for _ in range(self.max - len(self.loading)):
                down = self.queue.next()
                if down:
                    down.download()
                    self.loading.append(down)
                else:
                    break
            sleep(1)



