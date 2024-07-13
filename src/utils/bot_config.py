from aiogram import Bot
from aiogram.types import ChatAdministratorRights, BotCommand


async def base_configure_bot(bot: Bot) -> None:
    default_rights = ChatAdministratorRights(
        is_anonymous=False,
        can_delete_stories=True,
        can_edit_stories=True,
        can_post_stories=True,
        can_restrict_members=True,
        can_promote_members=True,
        can_manage_video_chats=True,
        can_invite_users=True,
        can_manage_chat=True,
        can_delete_messages=True,
        can_change_info=True,
        can_post_messages=True,
        can_edit_messages=True,
        can_pin_messages=True,
        can_manage_topics=True,
    )
    await bot.set_my_default_administrator_rights(default_rights)

    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="check_state", description="check state of group chat"),
        BotCommand(
            command="init", description="Bind this bot to your group and your id"
        ),
        BotCommand(command="set_api_key", description="set your API key"),
        BotCommand(command="set_log_chat", description="enable logging"),
        BotCommand(command="xadd", description="Add x.com username"),
        BotCommand(command="disc", description="Discover tweets"),
        BotCommand(command="help", description="Get help"),
    ]
    await bot.set_my_commands(commands)
