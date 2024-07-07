from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.deep_linking import create_startgroup_link

router = Router()


@router.message(Command("start"))
async def start(message: Message, bot: Bot):
    await message.answer(
        f"Hello, {message.from_user.full_name}! Invite me to your fresh supergroup using"
        f' <a href="{await create_startgroup_link(bot, "_")}">this link</a>\n\n'
        f'To check help use /help'
    )


# TODO: add help
@router.message(Command("help"))
async def help(message: Message):
    help = """
    Add this bot to your supergroup
    bot asks you to provide admin rights - you provide it, no jokes
    if no, manually give it admin rights, it will be already configured
    with needed permissions
    """
    await message.answer('')
