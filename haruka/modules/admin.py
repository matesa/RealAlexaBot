import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown, mention_html

from haruka import dispatcher, updater
from haruka.modules.disable import DisableAbleCommandHandler
from haruka.modules.helper_funcs.chat_status import bot_admin, can_promote, user_admin, can_pin, user_can_restrict, user_can_pin, user_can_change
from haruka.modules.helper_funcs.extraction import extract_user
from haruka.modules.log_channel import loggable
from haruka.modules.sql import admin_sql as sql
from haruka.modules.translations.strings import tld

from haruka.modules.connection import connected

@run_async
@bot_admin
@user_can_restrict
@loggable
def promote(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    conn = connected(bot, update, chat, user.id)
    if not conn == False:
        chatD = dispatcher.bot.getChat(conn)
    else:
        chatD = update.effective_chat
        if chat.type == "private":
            exit(1)

    if not chatD.get_member(bot.id).can_promote_members:
        update.effective_message.reply_text("I can't promote/demote people here! "
                                            "Make sure I'm admin and can appoint new admins.")
        exit(1)

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(tld(chat.id, "You don't seem to be referring to a user."))
        return ""

    user_member = chatD.get_member(user_id)
    if user_member.status == 'administrator' or user_member.status == 'creator':
        message.reply_text(tld(chat.id, "How am I meant to promote someone that's already an admin?"))
        return ""

    if user_id == bot.id:
        message.reply_text(tld(chat.id, "I can't promote myself! Get an admin to do it for me."))
        return ""

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chatD.get_member(bot.id)

    bot.promoteChatMember(chatD.id, user_id,
                          can_change_info=bot_member.can_change_info,
                          can_post_messages=bot_member.can_post_messages,
                          can_edit_messages=bot_member.can_edit_messages,
                          can_delete_messages=bot_member.can_delete_messages,
                          #can_invite_users=bot_member.can_invite_users,
                          can_restrict_members=bot_member.can_restrict_members,
                          can_pin_messages=bot_member.can_pin_messages)
                    

    message.reply_text(tld(chat.id, f"Successfully promoted in *{chatD.title}*!"), parse_mode=ParseMode.MARKDOWN)
    return f"<b>{html.escape(chatD.title)}:</b>" \
            "\n#PROMOTED" \
           f"\n<b>Admin:</b> {mention_html(user.id, user.first_name)}" \
           f"\n<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"


@run_async
@bot_admin
@user_can_restrict
@loggable
def demote(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    conn = connected(bot, update, chat, user.id)
    if not conn == False:
        chatD = dispatcher.bot.getChat(conn)
    else:
        chatD = update.effective_chat
        if chat.type == "private":
            exit(1)

    if not chatD.get_member(bot.id).can_promote_members:
        update.effective_message.reply_text("I can't promote/demote people here! "
                                            "Make sure I'm admin and can appoint new admins.")
        exit(1)

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(tld(chat.id, "You don't seem to be referring to a user."))
        return ""

    user_member = chatD.get_member(user_id)
    if user_member.status == 'creator':
        message.reply_text(tld(chat.id, "This person CREATED the chat, how would I demote them?"))
        return ""

    if not user_member.status == 'administrator':
        message.reply_text(tld(chat.id, "Can't demote what wasn't promoted!"))
        return ""

    if user_id == bot.id:
        message.reply_text(tld(chat.id, "I can't demote myself!"))
        return ""

    try:
        bot.promoteChatMember(int(chatD.id), int(user_id),
                              can_change_info=False,
                              can_post_messages=False,
                              can_edit_messages=False,
                              can_delete_messages=False,
                              can_invite_users=False,
                              can_restrict_members=False,
                              can_pin_messages=False,
                              can_promote_members=False)
        message.reply_text(tld(chat.id, f"Successfully demoted in *{chatD.title}*!"), parse_mode=ParseMode.MARKDOWN)
        return f"<b>{html.escape(chatD.title)}:</b>" \
                "\n#DEMOTED" \
               f"\n<b>Admin:</b> {mention_html(user.id, user.first_name)}" \
               f"\n<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"

    except BadRequest:
        message.reply_text(
            tld(chat.id, "Could not demote. I might not be admin, or the admin status was appointed by another user, so I can't act upon them!")
            )
        return ""


@run_async
@bot_admin
@user_can_pin
@loggable
def pin(bot: Bot, update: Update, args: List[str]) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    is_group = chat.type != "private" and chat.type != "channel"

    prev_message = update.effective_message.reply_to_message

    is_silent = True
    if len(args) >= 1:
        is_silent = not (args[0].lower() == 'notify' or args[0].lower() == 'loud' or args[0].lower() == 'violent')

    if prev_message and is_group:
        try:
            bot.pinChatMessage(chat.id, prev_message.message_id, disable_notification=is_silent)
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        return f"<b>{html.escape(chat.title)}:</b>" \
                "\n#PINNED" \
               f"\n<b>Admin:</b> {mention_html(user.id, user.first_name)}"

    return ""


@run_async
@bot_admin
@user_can_pin
@loggable
def unpin(bot: Bot, update: Update) -> str:
    chat = update.effective_chat
    user = update.effective_user  # type: Optional[User]

    try:
        bot.unpinChatMessage(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise

    return f"<b>{html.escape(chat.title)}:</b>" \
           "\n#UNPINNED" \
           f"\n<b>Admin:</b> {mention_html(user.id, user.first_name)}"


@run_async
@bot_admin
@user_can_change
def invite(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    conn = connected(bot, update, chat, user.id, need_admin=False)
    if not conn == False:
        chatP = dispatcher.bot.getChat(conn)
    else:
        chatP = update.effective_chat
        if chat.type == "private":
            exit(1)

    if chatP.username:
        update.effective_message.reply_text(chatP.username)
    elif chatP.type == chatP.SUPERGROUP or chatP.type == chatP.CHANNEL:
        bot_member = chatP.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = chatP.invite_link
            #print(invitelink)
            if not invitelink:
                invitelink = bot.exportChatInviteLink(chatP.id)

            update.effective_message.reply_text(invitelink)
        else:
            update.effective_message.reply_text(tld(chat.id, "I don't have access to the invite link, try changing my permissions!"))
    else:
        update.effective_message.reply_text(tld(chat.id, "I can only give you invite links for supergroups and channels, sorry!"))


@run_async
@user_admin
def adminlist(bot: Bot, update: Update):
    chat = update.effective_chat
    administrators = update.effective_chat.get_administrators()
    text = tld(chat.id, "Admins in *{}*:").format(
        update.effective_chat.title
        or tld(chat.id, "This chat").lower())
    for admin in administrators:
        user = admin.user
        name = "[{}](tg://user?id={})".format(user.first_name, user.id)
        if user.username:
            esc = escape_markdown("@" + user.username)
            name = "[{}](tg://user?id={})".format(esc, user.id)
        text += "\n - {}".format(name)

    update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)



@user_admin
@run_async
def reaction(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    if len(args) >= 1:
        var = args[0]
        print(var)
        if var == "False":
            sql.set_command_reaction(chat.id, False)
            update.effective_message.reply_text("Disabled reaction on admin commands for users")
        elif var == "True":
            sql.set_command_reaction(chat.id, True)
            update.effective_message.reply_text("Enabled reaction on admin commands for users")
        else:
            update.effective_message.reply_text("Please enter True or False!", parse_mode=ParseMode.MARKDOWN)
    else:
        status = sql.command_reaction(chat.id)
        if status == False:
            update.effective_message.reply_text("Reaction on admin commands for users now `disabled`!", parse_mode=ParseMode.MARKDOWN)
        else:
            update.effective_message.reply_text("Reaction on admin commands for users now `enabled`!", parse_mode=ParseMode.MARKDOWN)
        
__help__ = """
 - /adminlist | /admins: list of admins in the chat
 - /users: list all the users in the chat
 - /pin | /unpin: pins/unpins the message in the chat
 - /invitelink: gets invitelink
 - /promote: promotes a user 
 - /demote: demotes a user
 - /zombies: count the number of deleted account in your group
 - /kickthefools: kicks all members inactive from 1 week
 - /report <reason> | @admin: reply to a message to report it to admins(non-admin only)
 - /reports <on/off>: change report setting
 - /ban: bans a user 
 - /tban <d/h/m> : temporarily bans a user from your chat
 - /unban: unbans a user 
 - /sban: silently bans a user
 - /mute: mute a user 
 - /tmute <d/h/m>: temporarily mute a user
 - /unmute: unmutes a user
 - /kick: kicks a user 
 - /setflood <number/off>: set the number of messages to take action on a user for flooding
 - /setfloodmode <mute/ban/kick/tban/tmute>: select the valid action eg. /setfloodmode tmute 5m.
 - /flood: gets the current antiflood settings
 - /addblacklist <trigger> : blacklists the trigger
 - /unblacklist <trigger> | rmblacklist <trigger> : stop blacklisting a certain blacklist trigger
 - /blacklist: list all active blacklist filters
 - /addblacklist "the admins suck" respect your admins: This will remove the text everytime someone types it
 - /addblacklist `"bit.ly/*"`: This will remove the link everytime someone sends it matching `bit.ly`
 - /filter <word> <message>: Every time someone says "word", the bot will reply with "message"
 - /stop <word>: stop that filter.
 - /filters: list all active filters in this chat.
 - /connection <chatid>: Connect to remote chat
 - /disconnect: Disconnect from chat
 - /allowconnect on/yes/off/no: Allow connect users to group
 - /lock <item(s)>: lock the usage of "item" for non-admins
 - /unlock <item(s)>: unlock "item". Everyone can use them again
 - /locks: list the lock status in the chat
 - /locktypes: gets a list of all things that can be locked
 - /setlog: set a log channel.
 - /unsetlog: unset the log channel.
 - /logchannel: get the log channel info
 - /purge: deletes all messages from the message you replied to
 - /purge X: deletes X messages after the message you replied to 
 - /del: deletes the message you replied to.
 - /save <word> <sentence>: Save that sentence to the note called "word"
 - /get <word> | #<word> : get the note registered to that word
 - /clear <word>: delete the note called "word"
 - /notes | /saved: List all notes in the chat
 - /setrules <rules>: set the rules for this chat
 - /clearrules: clear the rules for this chat
 - /rules: get the rules for this chat
 - /addurl <url>: Add a domain to the blacklist, the bot will automatically parse the url
 - /delurl <url>: Remove url from the blacklist
 - /warn <userhandle>: warn a user
 - /resetwarn @username: reset the warnings for a user
 - /addwarn <word> <message>: set a warning filter on a certain word
 - /nowarn <word>: stop a warning filter
 - /warnlimit <num>: set the max warning limit
 - /warns <userhandle>: get a user's number, and reason, of warnings
 - /warnlist: list of all current warning filters
 - /strongwarn <on/yes/off/no>: exceeding warn limit will result in kick, if set to true will ban instead
 - /welcome <on/off/yes/no>: Will the bot welcome new members ?
 - /goodbye <on/off/yes/no>: Will the bid farewell when someone leave ?
 - /setwelcome <message>: set the welcome message 
 - /resetwelcome: clear the welcome message 
 - /setgoodbye <message>: set the goodbye message
 - /resetgoodbye: clear the goodbye message 
 - /cleanwelcome <on/off/yes/no>: clean welcome message 
 - /cleanservice <on/off/yes/no>: clean all service messages
 - /welcomesecurity <off/soft/hard>: check is the user joined is bot or not by prompting them to click on a button
"""

__mod_name__ = "Admin 🚫"

PIN_HANDLER = DisableAbleCommandHandler("pin", pin, pass_args=True, filters=Filters.group)
UNPIN_HANDLER = DisableAbleCommandHandler("unpin", unpin, filters=Filters.group)

INVITE_HANDLER = CommandHandler("invitelink", invite)

PROMOTE_HANDLER = DisableAbleCommandHandler("promote", promote, pass_args=True)
DEMOTE_HANDLER = DisableAbleCommandHandler("demote", demote, pass_args=True)

# REACT_HANDLER = DisableAbleCommandHandler("reaction", reaction, pass_args=True, filters=Filters.group)

ADMINLIST_HANDLER = DisableAbleCommandHandler(["adminlist", "admins"], adminlist)

dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(ADMINLIST_HANDLER)
# dispatcher.add_handler(REACT_HANDLER)
