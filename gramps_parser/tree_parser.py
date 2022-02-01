from render import draw
from db import Database
from loguru import logger


if __name__ == '__main__':
    logger.info('Start')
    db = Database('/home/rahmaevao/.gramps/grampsdb/61d89dd1')  # Янашбеляк
    # db = Database('/home/rahmaevao/.gramps/grampsdb/61ee61ab')  # Тест
    logger.info('The database has been read')
    draw(db)
