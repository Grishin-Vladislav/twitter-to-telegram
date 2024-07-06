from datetime import datetime

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, ForumTopic
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from src.database.models import Config

router = Router()


@router.message(Command("check_state"))
async def check_state(message: Message):
    forum = ' ' if message.chat.is_forum else ' not '
    topics = 'enabled' if message.chat.is_forum else 'disabled'
    await message.answer(
        f"chat type is {message.chat.type} and chat is{forum}a forum (has topics {topics})\n\n"
        f"currently admin status can not be checked, but be sure to give bot admin permissions to work properly!\n\n"
        f"If you checked everything, you can bind this bot to your id and group, "
        f"make sure to run it in desired supergroup /init"
    )


@router.message(Command("init"))
async def initialize(message: Message, session: Session):
    config = session.scalars(select(Config).where(Config.main_chat_id == message.chat.id)).first()

    if config:
        await message.answer("Config already exists, please use /set_api_key to set new API key")
        return

    try:
        log_topic: ForumTopic = await message.bot.create_forum_topic(
            name="logs", chat_id=message.chat.id
        )
    except:
        await message.answer("Something went wrong creating logs topic, please check bot permissions")
        return

    config = Config(
        main_chat_id=message.chat.id,
        log_thread_id=log_topic.message_thread_id,
        last_discovering_date=datetime.now()
    )

    try:
        session.add(config)
        session.commit()
        await message.answer(
            "Config saved, for bot to work, "
            "you need to set your Apify API key with /set_api_key + your API key"
        )
    except:
        session.rollback()
        await message.answer("Something went wrong")
        return


@router.message(Command("set_api_key"))
async def set_api_key(message: Message, command: CommandObject, session: Session):
    await message.delete()

    if not command.args:
        await message.answer("Key was not provided\n\n Example: /set_api_key 12345")
        return

    api_key = str(command.args)

    try:
        query = select(Config).where(Config.main_chat_id == message.chat.id)
        config: Config = session.scalars(query).one()
        config.apify_key = api_key
        session.commit()
        await message.bot.send_message(
            chat_id=config.main_chat_id,
            message_thread_id=config.log_thread_id,
            text=f"API key was set for this chat"
        )
    except NoResultFound:
        await message.answer(
            "Config not found for this chat, make sure to run /init first\n"
            "Or check that you are using this command in desired supergroup"
        )
        return
    except Exception as e:
        session.rollback()
        await message.answer(
            f"Something went wrong: {e}\n"
        )
        return
