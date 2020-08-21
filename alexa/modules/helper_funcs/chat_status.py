from functools import wraps
from typing import Optional
from telegram import User, Chat, ChatMember, Update, Bot
from alexa import DEL_CMDS, SUDO_USERS, WHITELIST_USERS
import alexa.modules.sql.admin_sql as admin_sql
from alexa.modules.translations.strings import tld
import sys
import traceback
from telegram import error

from alexa import DEL_CMDS, SUDO_USERS, WHITELIST_USERS


def can_delete(chat: Chat, bot_id: int) -> bool:
    return chat.get_member(bot_id).can_delete_messages


def is_user_ban_protected(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    if chat.type == 'private' \
            or user_id in SUDO_USERS \
            or user_id in WHITELIST_USERS \
            or chat.all_members_are_administrators:
        return True

    if not member:
        member = chat.get_member(user_id)
    return member.status in ('administrator', 'creator')

def is_user_admin(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
	if chat.type == 'private' \
			or user_id in SUDO_USERS \
			or chat.all_members_are_administrators or user_id == 777000:
		return True

	try:
		if not member:
			member = chat.get_member(user_id)
		return member.status in ('administrator', 'creator')
	except:
		return False

def is_bot_admin(chat: Chat, bot_id: int, bot_member: ChatMember = None) -> bool:
    if chat.type == 'private' \
            or chat.all_members_are_administrators:
        return True

    if not bot_member:
        bot_member = chat.get_member(bot_id)
    return bot_member.status in ('administrator', 'creator')


def is_user_in_chat(chat: Chat, user_id: int) -> bool:
    member = chat.get_member(user_id)
    return member.status not in ('left', 'kicked')


def bot_can_delete(func):
    @wraps(func)
    def delete_rights(bot: Bot, update: Update, *args, **kwargs):
        if can_delete(update.effective_chat, bot.id):
            return func(bot, update, *args, **kwargs)
        else:
            return
    return delete_rights


def can_pin(func):
    @wraps(func)
    def pin_rights(bot: Bot, update: Update, *args, **kwargs):
        if update.effective_chat.get_member(bot.id).can_pin_messages:
            return func(bot, update, *args, **kwargs)
        else:
            return
    return pin_rights


def can_promote(func):
    @wraps(func)
    def promote_rights(bot: Bot, update: Update, *args, **kwargs):
        if update.effective_chat.get_member(bot.id).can_promote_members:
            return func(bot, update, *args, **kwargs)
        else:
            return
    return promote_rights


def can_restrict(func):
    @wraps(func)
    def promote_rights(bot: Bot, update: Update, *args, **kwargs):
        if update.effective_chat.get_member(bot.id).can_restrict_members:
            return func(bot, update, *args, **kwargs)
        else:
            return
    return promote_rights


def bot_admin(func):
    @wraps(func)
    def is_admin(bot: Bot, update: Update, *args, **kwargs):
        if is_bot_admin(update.effective_chat, bot.id):
            return func(bot, update, *args, **kwargs)
        else:
            return
    return is_admin

def user_admin(func):
    @wraps(func)
    def is_admin(bot: Bot, update: Update, *args, **kwargs):
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        if user and is_user_admin(update.effective_chat, user.id):
            return func(bot, update, *args, **kwargs)

        elif not user:
            pass

        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()

        elif (admin_sql.command_reaction(chat.id) == True):
            return
    return is_admin


def user_admin_no_reply(func):
    @wraps(func)
    def is_admin(bot: Bot, update: Update, *args, **kwargs):
        user = update.effective_user  # type: Optional[User]
        if user and is_user_admin(update.effective_chat, user.id):
            return func(bot, update, *args, **kwargs)

        elif not user:
            pass

        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()

    return is_admin


def user_not_admin(func):
    @wraps(func)
    def is_not_admin(bot: Bot, update: Update, *args, **kwargs):
        user = update.effective_user  # type: Optional[User]
        if user and not is_user_admin(update.effective_chat, user.id):
            return func(bot, update, *args, **kwargs)

    return is_not_admin


def user_can_ban(func):
    @wraps(func)
    def user_is_banhammer(bot: Bot, update: Update, *args, **kwargs):
        user = update.effective_user.id
        member = update.effective_chat.get_member(user)
        if not (member.can_restrict_members or member.status == "creator"):          
            return ""
        return func(bot, update, *args, **kwargs)
    
    return user_is_banhammer

def user_can_restrict(func):
    @wraps(func)
    def user_is_restrict(bot: Bot, update: Update, *args, **kwargs):
        user = update.effective_user.id
        member = update.effective_chat.get_member(user)
        if not (member.can_promote_members or member.status == "creator"):          
            return ""
        return func(bot, update, *args, **kwargs)
    
    return user_is_restrict

def user_can_pin(func):
    @wraps(func)
    def user_pin_can(bot: Bot, update: Update, *args, **kwargs):
        user = update.effective_user.id
        member = update.effective_chat.get_member(user)
        if not (member.can_pin_messages or member.status == "creator"):      
            return ""
        return func(bot, update, *args, **kwargs)
    
    return user_pin_can


def user_can_delete(func):
    @wraps(func)
    def user_delete(bot: Bot, update: Update, *args, **kwargs):
        user = update.effective_user.id
        member = update.effective_chat.get_member(user)
        if not (member.can_delete_messages or member.status == "creator"):        
            return ""
        return func(bot, update, *args, **kwargs)
    
    return user_delete

def user_can_change(func):
    @wraps(func)
    def user_change(bot: Bot, update: Update, *args, **kwargs):
        user = update.effective_user.id
        member = update.effective_chat.get_member(user)
        if not (member.can_change_info or member.status == "creator"):
            return ""
        return func(bot, update, *args, **kwargs)
    
    return user_change
