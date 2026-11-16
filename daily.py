"""Daily money: cash, Pochi, M-Pesa, money used for goods, money drawn."""
from database import db
from helpers import check_date, num, today


def save_daily(data):
    d = check_date(data.get("date") or today())
    vals = (num(data.get("cash"), "Cash"), num(data.get("pochi"), "Pochi"), num(data.get("mpesa"), "M-Pesa"),
            num(data.get("spent"), "Money used for goods"), num(data.get("drawn"), "Money drawn"))
    with db() as con:
        existed = con.execute("SELECT 1 FROM daily WHERE date=?", (d,)).fetchone() is not None
        con.execute(
            "INSERT INTO daily(date,cash,pochi,mpesa,spent,drawn) VALUES (?,?,?,?,?,?) "
            "ON CONFLICT(date) DO UPDATE SET cash=excluded.cash, pochi=excluded.pochi, "
            "mpesa=excluded.mpesa, spent=excluded.spent, drawn=excluded.drawn", (d,) + vals)
    return {"updated": existed, "total": sum(vals[:3])}


def get_daily(d):
    d = check_date(d)
    with db() as con:
        r = con.execute("SELECT * FROM daily WHERE date=?", (d,)).fetchone()
        if r:
            return {"exists": True, **dict(r)}
        spent = con.execute("SELECT COALESCE(SUM(buy*qty),0) FROM purchases WHERE date=?", (d,)).fetchone()[0]
    return {"exists": False, "date": d, "cash": "", "pochi": "", "mpesa": "", "spent": spent, "drawn": ""}


def recent_daily(limit=14):
    with db() as con:
        rows = con.execute(
            "SELECT date,cash,pochi,mpesa,cash+pochi+mpesa AS total,spent,drawn "
            "FROM daily ORDER BY date DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]
