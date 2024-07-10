from typing import Any

from aiogram import Router
from aiogram.enums import ChatMemberStatus
from aiogram.types import ChatMemberUpdated
from aiogram import F

router = Router()


@router.my_chat_member(
    F.new_chat_member.status.in_(
        (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR)
    )
)
async def handle_adding_bot_to_group(chat_member: ChatMemberUpdated) -> Any:
    if (
        chat_member.chat.type != "supergroup"
        or not chat_member.chat.is_forum
        or chat_member.new_chat_member.status == ChatMemberStatus.MEMBER
    ):
        await chat_member.answer(
            f"chat type - <b>{chat_member.chat.type}</b>\n"
            f"chat is a forum (threads enabled) - "
            f"<b>{'True' if chat_member.chat.is_forum else 'False'}</b>\n"
            f"bot is admin - "
            f"<b>{'True' if chat_member.new_chat_member.status == ChatMemberStatus.ADMINISTRATOR else 'False'}</b>\n"
            f"For bot to work properly, please give this bot admin permissions, "
            f"ensure that chat a supergroup and enable threads in it\n\n"
            f"check again with /check_state"
        )
    else:
        await chat_member.answer(
            "Current state of chat is valid, "
            "please do not disable threads in this forum for bot to work properly"
        )
