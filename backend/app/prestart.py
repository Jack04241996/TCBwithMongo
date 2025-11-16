import logging, asyncio
from tenacity import retry, stop_after_attempt, wait_fixed, before_log, after_log
from app.core.db import ping, ensure_indexes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prestart")

@retry(
    stop=stop_after_attempt(60*5),   # 最多 5 分鐘
    wait=wait_fixed(1),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def _wait_mongo():
    asyncio.run(ping())

def main():
    logger.info("Pre-start: waiting for Mongo...")
    _wait_mongo()
    logger.info("Mongo is up. Ensuring indexes...")
    asyncio.run(ensure_indexes())
    logger.info("Pre-start done.")

if __name__ == "__main__":
    main()
