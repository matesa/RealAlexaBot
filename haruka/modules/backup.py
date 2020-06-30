import json, time, os
from io import BytesIO
from typing import Optional

from telegram import MAX_MESSAGE_LENGTH, ParseMode, InlineKeyboardMarkup
from telegram import Message, Chat, Update, Bot
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async, Filters

import haruka.modules.sql.notes_sql as sql
from haruka import dispatcher, LOGGER, OWNER_ID, SUDO_USERS, TEMPORARY_DATA
from haruka.__main__ import DATA_IMPORT
from haruka.modules.helper_funcs.chat_status import user_admin
from haruka.modules.helper_funcs.misc import build_keyboard, revert_buttons
from haruka.modules.helper_funcs.msg_types import get_note_type
from haruka.modules.rules import get_rules
from haruka.modules.helper_funcs.string_handling import button_markdown_parser, make_time

# SQL
import haruka.modules.sql.antiflood_sql as antifloodsql
import haruka.modules.sql.blacklist_sql as blacklistsql
from haruka.modules.sql import cust_filters_sql as filtersql
from haruka.modules.sql import languages_sql as langsql
import haruka.modules.sql.locks_sql as locksql
from haruka.modules.locks import LOCK_TYPES
from haruka.modules.sql import notes_sql as notesql
from haruka.modules.sql import reporting_sql as reportsql
import haruka.modules.sql.rules_sql as rulessql
from haruka.modules.sql import warns_sql as warnssql
import haruka.modules.sql.welcome_sql as welcsql

from haruka.modules.connection import connected

from haruka.modules.helper_funcs.msg_types import Types
from haruka.modules.languages import tl
from haruka.modules.helper_funcs.alternate import send_message




@run_async
@user_admin
def export_data(update, context):
	msg = update.effective_message  # type: Optional[Message]
	user = update.effective_user  # type: Optional[User]

	chat_id = update.effective_chat.id
	chat = update.effective_chat
	current_chat_id = update.effective_chat.id
	chat_data = context.chat_data

	conn = connected(context.bot, update, chat, user.id, need_admin=True)
	if conn:
		chat = dispatcher.bot.getChat(conn)
		chat_id = conn
		chat_name = dispatcher.bot.getChat(conn).title
	else:
		if update.effective_message.chat.type == "private":
			send_message(update.effective_message, tld(update.effective_message, "You can do this command in group but not in PM"))
			return ""
		chat = update.effective_chat
		chat_id = update.effective_chat.id
		chat_name = update.effective_message.chat.title

	jam = time.time()
	new_jam = jam + 43200
	cek = get_chat(chat_id, chat_data)
	if cek.get('status'):
		if jam <= int(cek.get('value')):
			waktu = time.strftime("%H:%M:%S %d/%m/%Y", time.localtime(cek.get('value')))
			send_message(update.effective_message, tld(update.effective_message, "You can backup data once in 12 hours !\n[This Person](tg://user?id={}) has backed up data\nYou can backup data again in `{}`").format(cek.get('user'), waktu), parse_mode=ParseMode.MARKDOWN)
			return
		else:
			if user.id != OWNER_ID:
				put_chat(chat_id, user.id, new_jam, chat_data)
	else:
		if user.id != OWNER_ID:
			put_chat(chat_id, user.id, new_jam, chat_data)


	# Backup version
	# Revision: 07/07/2019
	backup_ver = 1
	bot_base = "Alexa"

	# Make sure this backup is for this bot
	bot_id = context.bot.id

	# Backuping antiflood
	flood_mode, flood_duration = antifloodsql.get_flood_setting(chat_id)
	flood_limit = antifloodsql.get_flood_limit(chat_id)
	antiflood = {'flood_mode': flood_mode, 'flood_duration': flood_duration, 'flood_limit': flood_limit}

	# Backuping blacklists
	all_blacklisted = blacklistsql.get_chat_blacklist(chat_id)
	blacklist_mode, blacklist_duration = blacklistsql.get_blacklist_setting(chat.id)
	blacklists = {'blacklist_mode': blacklist_mode, 'blacklist_duration': blacklist_duration, 'blacklists': all_blacklisted}


	# Backuping filters
	all_filters = filtersql.get_chat_triggers(chat_id)
	filters_gen = []
	for x in all_filters:
		filt = filtersql.get_filter(chat.id, x)
		if filt.is_sticker:
			filt_type = 1
		elif filt.is_document:
			filt_type = 2
		elif filt.is_image:
			filt_type = 3
		elif filt.is_audio:
			filt_type = 4
		elif filt.is_voice:
			filt_type = 5
		elif filt.is_video:
			filt_type = 6
		elif filt.has_markdown:
			filt_type = 0
		else:
			filt_type = 7
		filters_gen.append({"name": x, "reply": filt.reply, "type": filt_type})
	filters = {'filters': filters_gen}

	# Backuping greetings msg and config
	greetings = {}
	pref, welcome_m, cust_content, welcome_type = welcsql.get_welc_pref(chat_id)
	if not welcome_m:
		welcome_m = ""
	if not cust_content:
		cust_content = ""
	buttons = welcsql.get_welc_buttons(chat_id)
	welcome_m += revert_buttons(buttons)
	greetings["welcome"] = {"enable": pref, "text": welcome_m, "content": cust_content, "type": welcome_type}

	pref, goodbye_m, cust_content, goodbye_type = welcsql.get_gdbye_pref(chat_id)
	if not goodbye_m:
		goodbye_m = ""
	if not cust_content:
		cust_content = ""
	buttons = welcsql.get_gdbye_buttons(chat_id)
	goodbye_m += revert_buttons(buttons)
	greetings["goodbye"] = {"enable": pref, "text": goodbye_m, "content": cust_content, "type": goodbye_type}

	curr = welcsql.clean_service(chat_id)
	greetings["clean_service"] = curr

	getcur, cur_value, extra_verify, timeout, timeout_mode, cust_text = welcsql.welcome_security(chat_id)
	greetings["security"] = {"enable": getcur, "text": cust_text, "time": cur_value, "extra_verify": extra_verify, "timeout": timeout, "timeout_mode": timeout_mode}

	# Backuping chat language
	getlang = langsql.get_lang(chat_id)
	language = {"language": getlang}

	# Backuping locks
	curr_locks = locksql.get_locks(chat_id)
	curr_restr = locksql.get_restr(chat_id)

	if curr_locks:
		locked_lock = {
			"sticker": curr_locks.sticker,
			"audio": curr_locks.audio,
			"voice": curr_locks.voice,
			"document": curr_locks.document,
			"video": curr_locks.video,
			"contact": curr_locks.contact,
			"photo": curr_locks.photo,
			"gif": curr_locks.gif,
			"url": curr_locks.url,
			"bots": curr_locks.bots,
			"forward": curr_locks.forward,
			"game": curr_locks.game,
			"location": curr_locks.location,
			"rtl": curr_locks.rtl
		}
	else:
		locked_lock = {}

	if curr_restr:
		locked_restr = {
			"messages": curr_restr.messages,
			"media": curr_restr.media,
			"other": curr_restr.other,
			"previews": curr_restr.preview,
			"all": all([curr_restr.messages, curr_restr.media, curr_restr.other, curr_restr.preview])
		}
	else:
		locked_restr = {}

	lock_warn = locksql.get_lockconf(chat_id)

	locks = {'lock_warn': lock_warn, 'locks': locked_lock, 'restrict': locked_restr}

	# Backuping notes
	note_list = notesql.get_all_chat_notes(chat_id)
	notes = []
	for note in note_list:
		buttonlist = ""
		note_tag = note.name
		note_type = note.msgtype
		getnote = notesql.get_note(chat_id, note.name)
		if not note.value:
			note_data = ""
		else:
			tombol = notesql.get_buttons(chat_id, note_tag)
			keyb = []
			buttonlist = ""
			for btn in tombol:
				if btn.same_line:
					buttonlist += "[{}](buttonurl:{}:same)\n".format(btn.name, btn.url)
				else:
					buttonlist += "[{}](buttonurl:{})\n".format(btn.name, btn.url)
			note_data = "{}\n\n{}".format(note.value, buttonlist)
		note_file = note.file
		if not note_file:
			note_file = ""
		notes.append({"note_tag": note_tag, "note_data": note_data, "note_file": note_file, "note_type": note_type})

	# Backuping reports
	get_report = reportsql.user_should_report(chat_id)
	report = {'report': get_report}

	# Backuping rules
	getrules = rulessql.get_rules(chat_id)
	rules = {"rules": getrules}

	# Backuping warns config and warn filters
	warn_limit, _, warn_mode = warnssql.get_warn_setting(chat_id)
	all_handlers = warnssql.get_chat_warn_triggers(chat_id)
	all_warn_filter = []
	for x in all_handlers:
		warnreply = warnssql.get_warn_filter(chat_id, x)
		all_warn_filter.append({'name': x, 'reason': warnreply.reply})
	if not warn_mode:
		warn_mode = ""
	# Get all warnings in current chat
	allwarns = warnssql.get_allwarns(chat_id)
	warns = {"warn_limit": warn_limit, "warn_mode": warn_mode, "warn_filters": all_warn_filter, "chat_warns": allwarns}


	# Parsing backups
	backup = {"bot_id": bot_id, "bot_base": bot_base, "antiflood": antiflood, "blacklists": blacklists, "blstickers": blstickers, "disabled": disabled, "filters": filters, "greetings": greetings, "language": language, "locks": locks, "notes": notes, "report": report, "rules": rules, "warns": warns, "version": backup_ver}


	all_backups = json.dumps(backup, indent=4, cls=SetEncoder)
	f = open("{}-haruka.backup".format(chat_id), "w")
	f.write(str(all_backups))
	f.close()
	context.bot.sendChatAction(current_chat_id, "upload_document")
	tgl = time.strftime("%H:%M:%S - %d/%m/%Y", time.localtime(time.time()))
	try:
		context.bot.sendMessage(TEMPORARY_DATA, "*Successfully backed up for: *\Chat: Name: `{}`\nChat ID: `{}`\nOn: `{}`".format(chat.title, chat_id, tgl), parse_mode=ParseMode.MARKDOWN)
	except BadRequest:
		pass
	send = context.bot.sendDocument(current_chat_id, document=open('{}-Alexa.backup'.format(chat_id), 'rb'), caption=tld(update.effective_message, "*Successfully backed up for: *\nChat Name: `{}`\nChat ID: `{}`\nOn: `{}`\n\nNote: This backup is specific to this bot, if it is imported into another bot then the document, video, audio, voice, etc. will be lost").format(chat.title, chat_id, tgl), timeout=360, reply_to_message_id=msg.message_id, parse_mode=ParseMode.MARKDOWN)
	try:
		# Send to temp data for prevent unexpected issue
		context.bot.sendDocument(TEMPORARY_DATA, document=send.document.file_id, caption=tld(update.effective_message, "*Successfully backed up for: *\nChat Name: `{}`\nChat ID: `{}`\nOn: `{}`\n\nNote: This backup is specific to this bot, if it is imported into another bot then the document, video, audio, voice, etc. will be lost").format(chat.title, chat_id, tgl), timeout=360, parse_mode=ParseMode.MARKDOWN)
	except BadRequest:
		pass
	os.remove("{}-Alexa.backup".format(chat_id)) # Cleaning file


class SetEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, set):
			return list(obj)
		return json.JSONEncoder.default(self, obj)


# Temporary data
def put_chat(chat_id, user_id, value, chat_data):
	# print(chat_data)
	if value == False:
		status = False
	else:
		status = True
	chat_data[chat_id] = {'backups': {"status": status, "user": user_id, "value": value}}

def get_chat(chat_id, chat_data):
	# print(chat_data)
	try:
		value = chat_data[chat_id]['backups']
		return value
	except KeyError:
		return {"status": False, "user": None, "value": False}
