import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import BOT_TOKEN, DB_URL
from src.database.models import Base
from src.routers import start, chat_member, twitter, initialize_group
from src.schedule.make_discover import start_discovering_schedule
from src.utils import bot_config


async def main() -> None:
    dp = Dispatcher()
    dp.include_routers(
        start.router, chat_member.router, initialize_group.router, twitter.router
    )

    engine = create_engine(DB_URL, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    Base.metadata.create_all(engine)

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

    await bot_config.base_configure_bot(bot)

    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.gather(
        dp.start_polling(bot, session=session),
        start_discovering_schedule(session=session, bot=bot),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
