from manglib_parser import MangaLibBook, load_chapter
from composer import Composer

if __name__ == '__main__':

    composer = Composer()

    def printer(c):
        print(c, composer)

    book = MangaLibBook('ijiranaide-nagatoro-san')

    with open('n1.pdf', 'wb') as f:
        f.write(composer.urls2pdf(book.load(printer), printer))
    