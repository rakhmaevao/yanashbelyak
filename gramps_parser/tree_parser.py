from render import Render
from db import Database
from loguru import logger


if __name__ == '__main__':
    logger.info('Start')
    db = Database('/home/rahmaevao/.gramps/grampsdb/61ee61ab')
    logger.info('The database has been read')
    Render(db)
