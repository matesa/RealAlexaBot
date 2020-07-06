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
from haruka.modules.helper_funcs.chat_status import bot_admin, can_promote, user_admin, can_pin, user_can_restrict, user_can_pin
from haruka.modules.helper_funcs.extraction import extract_user
from haruka.modules.log_channel import loggable
from haruka.modules.sql import admin_sql as sql
from haruka.modules.translations.strings import tld

from haruka.modules.connection import connected

@run_async
@bot_admin
@user_can_restrict
@loggable
@can_promote
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
                          can_pin_messages=bot_member.can_pin_messages,
                          can_promote_members=bot_member.can_promote_members)

    message.reply_text(tld(chat.id, f"Successfully promoted in *{chatD.title}*!"), parse_mode=ParseMode.MARKDOWN)
    return f"<b>{html.escape(chatD.title)}:</b>" \
            "\n#PROMOTED" \
           f"\n<b>Admin:</b> {mention_html(user.id, user.first_name)}" \
           f"\n<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"


@run_async
@bot_admin
@user_can_restrict
@can_promote
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
@can_pin
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
@can_pin
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
@user_admin
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
def adminlist(bot, update):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    conn = connected(bot, update, chat, user.id, need_admin=False)
    if not conn == False:
        chatP = dispatcher.bot.getChat(conn)
    else:
        chatP = update.effective_chat
        if chat.type == "private":
            exit(1)
    
    administrators = chatP.get_administrators()

    text = tld(chat.id, "Admins in") + " *{}*:".format(chatP.title or tld(chat.id, "this chat"))
    for admin in administrators:
        user = admin.user
        status = admin.status
        if status == "creator":
            name = user.first_name + (user.last_name or "") + tld(chat.id, " (Creator)")
        else:
            name = user.first_name + (user.last_name or "")
        text += f"\n• `{name}`"

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
 - /users: List all the users in the chat
 - /pin: silently pins the message replied to - add 'loud' or 'notify' to give notifs to users.
 - /unpin: unpins the currently pinned message
 - /invitelink: gets invitelink
 - /promote: promotes the user replied to
 - /demote: demotes the user replied to
 - /zombies: Searches the number of deleted account in your group 
 - /zombies clean: Removes all deleted account from your group 
 - /kickthefools: Kicks all members who are inactive since 1 week
 - /report <reason>: reply to a message to report it to admins.
 - @admin: reply to a message to report it to admins [Non-Admins Only]
 - /reports <on/off>: change report setting, or view current status.
If done in pm, toggles your status.
If in chat, toggles that chat's status.
 - /rules: get the rules for this chat.
 - /setrules <your rules here>: set the rules for this chat.
 - /clearrules: clear the rules for this chat.
 - /ban: bans a user from your chat.
 - /banme: ban yourself
 - /tban: temporarily bans a user from your chat. set time using int<d/h/m> (days hours minutes)
 - /unban: unbans a user from your chat.
 - /sban: silently bans a user. (via handle, or reply)
 - /mute: mute a user in your chat.
 - /tmute: temporarily mute a user in your chat. set time using int<d/h/m> (days hours minutes)
 - /unmute: unmutes a user from your chat.
 - /kick: kicks a user from your chat.
 - /kickme: users who use this, kick themselves!
 - /unbanall: unbans everyone in the chat
 - /lock <item(s)>: lock the usage of "item". Now, only admins will be able to use this type!
 - /unlock <item(s)>: unlock "item". Everyone can use them again.
 - /locks: list the lock status in the chat.
 - /locktypes: gets a list of all things that can be locked. (have a look at this!)
 - /save <word> <sentence>: Save that sentence to the note called "word". Replying to a message will save that message. Even works on media!
 - /get <word>: get the note registered to that word.
 - #<word>: same as /get word
 - /clear <word>: delete the note called "word"
 - /notes: List all notes in the current chat
 - /saved: same as /notes
 - /purge: deletes all messages from the message you replied to, to the current message.
 - /purge X: deletes X messages after the message you replied to (including the replied message)
 - /del: deletes the message you replied to.
 - /warns <userhandle>: get a user's number, and reason, of warnings.
 - /warnlist: list of all current warning filters
 - /warn <userhandle>: warn a user. After 3 warns, the user will be banned from the group. Can also be used as a reply.
 - /resetwarn <userhandle>: reset the warnings for a user. Can also be used as a reply.
 - /addwarn <keyword> <reply message>: set a warning filter on a certain keyword. If you want your keyword to be a sentence, encompass it with quotes, as such: `/addwarn "very angry" This is an angry user`. 
 - /nowarn <keyword>: stop a warning filter
 - /warnlimit <num>: set the warning limit
 - /strongwarn <on/yes/off/no>: If set to on, exceeding the warn limit will result in a ban. Else, will just kick.
 - /welcome <on/off>: enable/disable welcome messages.
 - /welcome: shows current welcome settings.
 - /welcome noformat: shows current welcome settings, without the formatting - useful to recycle your welcome messages!
 - /goodbye -> same usage and args as /welcome.
 - /setwelcome <sometext>: set a custom welcome message. If used replying to media, uses that media.
 - /setgoodbye <sometext>: set a custom goodbye message. If used replying to media, uses that media.
 - /resetwelcome: reset to the default welcome message.
 - /resetgoodbye: reset to the default goodbye message.
 - /cleanwelcome <on/off>: On new member, try to delete the previous welcome message to avoid spamming the chat.
 - /wlcmutehelp: gives information about welcome mutes.
 - /welcomehelp: view more formatting information for custom welcome/goodbye messages.
 - /connection <chatid>: Connect to remote chat
 - /disconnect: Disconnect from chat
 - /allowconnect on/yes/off/no: Allow connect users to group
 - /addblacklist <blacklist trigger> <blacklist reason>: blacklists the trigger. You can set sentences by putting quotes around the reason.
 - /unblacklist <blacklist trigger>: stop blacklisting a certain blacklist trigger.
 - /rmblacklist <blacklist trigger>: same as /unblacklist
 - /blacklist: list all active blacklist filters
 - /addblacklist "the admins suck" Respect your admins!
This would delete any message containing 'the admins suck'.
If you've enabled an alternative blacklist mode, it will warn, ban, kick, or mute a user with a message specifying the reason.
 - /addblacklist "bit.ly/*" We dont like shorteners!
If you want to only match bit.ly/ links followed by three characters, you could use:
 - /addblacklist "bit.ly/???" We dont like shorteners!
This would match bit.ly/abc, but not bit.ly/abcd.
 - /addurl <urls>: Add a domain to the blacklist. The bot will automatically parse the url.
 - /delurl <urls>: Remove urls from the blacklist
 - /geturl: View the current blacklisted urls
 - /setlog: set a log channel.
 - /unsetlog: unset the log channel.
 - /logchannel: get the log channel info
Setting the log channel is done by:
▪️ adding the bot to the desired channel (as an admin!)
▪️ sending /setlog in the channel
▪️ forwarding the /setlog to the group
 - /filter <keyword> <reply message>: Every time someone says "word", the bot will reply with "sentence". For multiple word filters, quote the first word.
 - /stop <filter keyword>: stop that filter.
 - /filters: list all active filters in this chat.
 - /export: Takes a backup of your notes, filters, etc.. and sends the data as a backup file 
 - /import: Type in reply to the backup file to restore your chat data
"""

__mod_name__ = "Admin 🚫"

PIN_HANDLER = DisableAbleCommandHandler("pin", pin, pass_args=True, filters=Filters.group)
UNPIN_HANDLER = DisableAbleCommandHandler("unpin", unpin, filters=Filters.group)

INVITE_HANDLER = CommandHandler("invitelink", invite)

PROMOTE_HANDLER = DisableAbleCommandHandler("promote", promote, pass_args=True)
DEMOTE_HANDLER = DisableAbleCommandHandler("demote", demote, pass_args=True)

REACT_HANDLER = DisableAbleCommandHandler("reaction", reaction, pass_args=True, filters=Filters.group)

ADMINLIST_HANDLER = DisableAbleCommandHandler(["adminlist", "admins"], adminlist)

dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(ADMINLIST_HANDLER)
dispatcher.add_handler(REACT_HANDLER)
