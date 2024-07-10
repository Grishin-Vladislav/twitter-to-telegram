from aiogram import Router, F, Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, ForumTopic, CallbackQuery
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from src.database.models import Config, TwitterObject
from src.schedule.make_discover import discover_tweets

router = Router()


@router.message(Command("xadd"))
async def add_x(message: Message, command: CommandObject):
    x_url, twitter_url = "https://x.com/", "https://twitter.com/"
    if not command.args:
        await message.answer(
            f"you need to specify twitter username or url after command, "
            f"for example: /xadd elonmusk or /xadd {x_url}elonmusk"
        )
        return

    if command.args.startswith(x_url) or command.args.startswith(twitter_url):
        x_username = (
            command.args.replace(x_url, "").replace(twitter_url, "").rstrip("/")
        )
    else:
        x_username = command.args

    kb = InlineKeyboardBuilder()
    kb.button(text="yes", callback_data=f"xadd:{x_username}:yes")
    kb.button(text="no", callback_data=f"xadd:{x_username}:no")
    await message.answer(
        f"is this correct username: '{x_username}'?", reply_markup=kb.as_markup()
    )


@router.callback_query(F.data.startswith("xadd"))
async def resolve_add_x(callback_query: CallbackQuery, session: Session):
    message: Message = callback_query.message
    bot: Bot = message.bot
    _, username, user_answer = callback_query.data.split(":")
    await callback_query.answer()
    await message.edit_reply_markup(reply_markup=None)

    if user_answer == "yes":
        try:
            config = session.scalars(
                select(Config).where(Config.main_chat_id == message.chat.id)
            ).one()

            topic: ForumTopic = await bot.create_forum_topic(
                name=f"{username}", chat_id=message.chat.id
            )

            config.twitter_objects.append(
                TwitterObject(
                    twitter_username=username, thread_id=topic.message_thread_id
                )
            )
            session.add(config)
            session.commit()

            await bot.send_message(
                chat_id=message.chat.id,
                message_thread_id=topic.message_thread_id,
                text=f"{username} added",
            )

        except TelegramBadRequest as e:
            print(e)
            await bot.send_message(
                chat_id=callback_query.message.chat.id,
                text="something went wrong trying to create new topic (check bot permissions)",
            )

        except NoResultFound:
            await bot.send_message(
                chat_id=callback_query.message.chat.id,
                text="config not found for this chat, make sure to run /init first",
            )

        except Exception as e:
            session.rollback()
            await bot.send_message(
                chat_id=callback_query.message.chat.id,
                text=f"something went wrong: {e}",
            )

    else:
        await bot.send_message(chat_id=message.chat.id, text="better luck next time")


@router.message(Command("disc"))
async def list_x(message: Message, session: Session, bot: Bot):
    await discover_tweets(session, bot)
