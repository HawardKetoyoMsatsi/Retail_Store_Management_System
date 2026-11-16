"""Data for the Dashboard page and the app start-up."""
from datetime import date, timedelta

from config import STOCK_TAKE_WEEKDAY
from daily import recent_daily
from database import db
from helpers import STOCK_DAY_NAME, last_stock_day, next_stock_day, today
from catalog import items
from purchases import recent_purchases
from reconcile import reconcile
from settings import get_capital


def stock_status(con):
    """Is this week's stock take done? Drives the reminder banner."""
    due = last_stock_day()                       # today if today is the stock take day
    nxt = next_stock_day()
    any_goods = con.execute("SELECT 1 FROM purchases LIMIT 1").fetchone() is not None
    goods_by_due = con.execute("SELECT 1 FROM purchases WHERE date<=? LIMIT 1", (due,)).fetchone() is not None
    done = con.execute("SELECT 1 FROM stocktake WHERE date=? LIMIT 1", (due,)).fetchone() is not None
    if not any_goods:
        state, msg = "none", "Start by recording goods bought. Stock is counted every " + STOCK_DAY_NAME + "."
    elif not goods_by_due:
        state, msg = "upcoming", f"Next stock take: {STOCK_DAY_NAME} {nxt}."
    elif done:
        state, msg = "done", f"✓ Stock take for {due} is done. Next one: {STOCK_DAY_NAME} {nxt}."
    elif due == today():
        state, msg = "due", f"Today is stock take day. Count the shelves and enter the quantities."
    else:
        state, msg = "overdue", f"Stock take for {STOCK_DAY_NAME} {due} was not done. Enter it now (pick {due} as the date)."
    return {"state": state, "message": msg, "due_date": due, "next_date": nxt}


def dashboard():
    with db() as con:
        last = con.execute("SELECT MAX(date) FROM stocktake").fetchone()[0]
        stock_rows = con.execute(
            "SELECT item,qty,price,value FROM stocktake WHERE date=? ORDER BY value DESC", (last,)).fetchall() if last else []
        since = (date.today() - timedelta(days=13)).isoformat()
        buys = con.execute(
            "SELECT date, SUM(buy*qty) cost, SUM(sell*qty) sell_value FROM purchases "
            "WHERE date>=? GROUP BY date ORDER BY date", (since,)).fetchall()
        totals = con.execute(
            "SELECT (SELECT COUNT(*) FROM catalog), COALESCE(SUM(buy*qty),0), COALESCE(SUM(sell*qty),0) FROM purchases").fetchone()
        status = stock_status(con)
    daily = recent_daily(14)
    return {
        "today": today(),
        "stock_status": status,
        "rec": reconcile(last or today()),
        "last_stocktake": last or "",
        "stock_rows": [dict(r) for r in stock_rows],
        "money_trend": list(reversed(daily)),
        "buy_trend": [dict(r) for r in buys],
        "item_count": totals[0],
        "all_cost": totals[1],
        "all_selling": totals[2],
        "money_now": daily[0] if daily else None,
        "recent_purchases": recent_purchases(6),
        "recent_daily": daily[:6],
    }


def init_payload():
    return {
        "today": today(),
        "capital": get_capital(),
        "items": items(),
        "stock_day_name": STOCK_DAY_NAME,
        "stock_day_js": (STOCK_TAKE_WEEKDAY + 1) % 7,   # JavaScript: Sunday = 0
        "default_stock_date": last_stock_day(),
    }
