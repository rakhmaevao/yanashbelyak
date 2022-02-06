from render import Render
from db import Database
from loguru import logger
import os


if __name__ == '__main__':
    logger.info('Start')
    db = Database('/home/rahmaevao/.gramps/grampsdb/61d89dd1')  # Янашбеляк
    # db = Database('/home/rahmaevao/.gramps/grampsdb/61ee61ab')  # Тест
    logger.info('The database has been read')


    if 'content' in set(os.listdir()):
        output_path = "content/images/tree.svg"
    else:
        output_path = "../content/images/tree.svg"
    Render(db, output_path)
