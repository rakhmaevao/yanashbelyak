from render import Render
from db import Database
from loguru import logger


if __name__ == '__main__':
    logger.info('Start')
    db = Database()
    logger.info('The database has been read')
    Render(db)
