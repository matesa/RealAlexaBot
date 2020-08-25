#  This is made by @AyushChatterjee
#  If you kang this without credits I swear ur mom will die 

import threading
from sqlalchemy import Column, UnicodeText, Boolean, Integer
from alexa.modules.sql import BASE, SESSION

class APPROVE(BASE):
    __tablename__ = "approved_users"

    user_id = Column(Integer, primary_key=True)
    is_approved = Column(Boolean)
    reason = Column(UnicodeText)

    def __init__(self, user_id, reason="", is_approved=True):
        self.user_id = user_id
        self.reason = reason
        self.is_approved = is_approved

    def __repr__(self):
        return "approved_status for {}".format(self.user_id)

APPROVE.__table__.create(checkfirst=True)
INSERTION_LOCK = threading.RLock()

APPROVED_USERS = {}

def is_approved(user_id):
    return user_id in APPROVED_USERS

def check_APPROVE_status(user_id):
    try:
        return SESSION.query(APPROVE).get(user_id)
    finally:
        SESSION.close()

def set_APPROVE(user_id, reason=""):
    with INSERTION_LOCK:
        curr = SESSION.query(APPROVE).get(user_id)
        if not curr:
            curr = APPROVE(user_id, reason, True)
        else:
            curr.is_approved = True

        APPROVED_USERS[user_id] = reason

        SESSION.add(curr)
        SESSION.commit()

def rm_APPROVE(user_id):
    with INSERTION_LOCK:
        curr = SESSION.query(APPROVE).get(user_id)
        if curr:
            if user_id in APPROVED_USERS:  # sanity check
                del APPROVED_USERS[user_id]

            SESSION.delete(curr)
            SESSION.commit()
            return True

        SESSION.close()
        return False

def toggle_APPROVE(user_id, reason=""):
    with INSERTION_LOCK:
        curr = SESSION.query(APPROVE).get(user_id)
        if not curr:
            curr = APPROVE(user_id, reason, True)
        elif curr.is_approved:
            curr.is_approved = False
        elif not curr.is_approved:
            curr.is_approved = True
        SESSION.add(curr)
        SESSION.commit()

def __load_APPROVE_users():
    global APPROVED_USERS
    try:
        all_APPROVE = SESSION.query(APPROVE).all()
        APPROVED_USERS = {user.user_id: user.reason for user in all_APPROVE if user.is_approved}
    finally:
        SESSION.close()

__load_APPROVE_users()
