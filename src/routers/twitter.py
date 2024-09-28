from aiogram import Router, F, Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, ForumTopic, CallbackQuery, user
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

    if not message.message_thread_id:
        await bot.send_message(
            chat_id=message.chat.id, text="you can't add users in general thread"
        )
        return

    _, username, user_answer = callback_query.data.split(":")
    await callback_query.answer()
    await message.edit_reply_markup(reply_markup=None)

    if user_answer == "yes":
        try:
            config = session.scalars(
                select(Config).where(Config.main_chat_id == message.chat.id)
            ).one()

            target_thread_id = message.message_thread_id

            config.twitter_objects.append(
                TwitterObject(twitter_username=username, thread_id=target_thread_id)
            )
            session.add(config)
            session.commit()

            await message.reply(
                text=f"{username} added",
            )

        except TelegramBadRequest as e:
            print(e)
            await bot.send_message(
                chat_id=message.chat.id,
                text="something went wrong trying to create new topic (check bot permissions)",
            )

        except NoResultFound:
            await bot.send_message(
                chat_id=message.chat.id,
                text="config not found for this chat, make sure to run /init first",
            )

        except Exception as e:
            session.rollback()
            await bot.send_message(
                chat_id=message.chat.id,
                text=f"something went wrong: {e}",
            )

    else:
        await bot.send_message(chat_id=message.chat.id, text="better luck next time")


@router.message(Command("disc"))
async def list_x(message: Message, session: Session, bot: Bot):
    await discover_tweets(session, bot)


@router.message(Command("xlist"))
async def list_users(message: Message, session: Session):
    if not message.message_thread_id:
        config = session.scalars(
            select(Config).where(Config.main_chat_id == message.chat.id)
        ).one()

        usernames = "\n".join(
            (
                f"{idx}. <b>{str(username)}</b>"
                for idx, username in enumerate(config.twitter_objects)
            )
        )

        if not usernames:
            await message.answer("you don't have any listed xusers")
            return

        await message.answer(usernames)

    else:
        stmt = select(TwitterObject).where(
            TwitterObject.thread_id == message.message_thread_id
        )

        users = session.scalars(stmt).all()
        usernames = "\n".join(
            (f"{idx}. <b>{str(user)}</b>" for idx, user in enumerate(users))
        )
        if not usernames:
            await message.answer("you don't have any listed xusers in this thread")
            return

        await message.answer(usernames)


@router.message(Command("xdel"))
async def remove_users(message: Message, session: Session, command: CommandObject):
    if not command.args:
        await message.answer(
            "you need to select one or more numbers, divided by space. "
            'for example, "/xdel 0 4 2 5". to show list use /xlist'
        )
        return

    user_input = command.args.split()

    for el in user_input:
        if not el.isdigit() or len(el) not in (1, 2):
            await message.answer("you shall not pass")
            return

    user_selected_nums = [int(num) for num in user_input]

    if not message.message_thread_id:
        config = session.scalars(
            select(Config).where(Config.main_chat_id == message.chat.id)
        ).one()

        users = config.twitter_objects

    else:
        stmt = select(TwitterObject).where(
            TwitterObject.thread_id == message.message_thread_id
        )
        users = session.scalars(stmt).all()

    ids_to_remove = []
    for num in user_selected_nums:
        try:
            user_id = users[num].id
            ids_to_remove.append(user_id)
        except KeyError:
            continue

    if ids_to_remove:
        session.query(TwitterObject).where(TwitterObject.id.in_(ids_to_remove)).delete()
    try:
        session.commit()
    except:
        session.rollback()
        await message.answer("something went wrong")

    await message.answer("Done!")
