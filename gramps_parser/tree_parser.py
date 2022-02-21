from render import Render
from db import Database
from biographer import Biographer
from loguru import logger
import os


if __name__ == '__main__':
    logger.info('Start')
    # db = Database('/home/rahmaevao/.gramps/grampsdb/61d89dd1')  # Янашбеляк
    db = Database('/home/rahmaevao/.gramps/grampsdb/61ee61ab')  # Тест
    logger.info('The database has been read')


    if 'content' in set(os.listdir()):
        content_dir = "content"
    else:
        content_dir = "../content"
    Render(db, f'{content_dir}/images/tree.svg')
    Biographer(db, content_dir)
