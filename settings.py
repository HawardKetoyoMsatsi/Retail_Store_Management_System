"""Business settings (opening capital)."""
from database import db
from helpers import num


def get_capital(con=None):
    if con is None:
        with db() as c:
            return get_capital(c)
    return con.execute("SELECT value FROM settings WHERE key='capital'").fetchone()[0]


def set_capital(data):
    with db() as con:
        con.execute("UPDATE settings SET value=? WHERE key='capital'", (num(data.get("capital"), "Capital"),))
        return {"capital": get_capital(con)}
