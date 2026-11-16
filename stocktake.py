"""Stock take: counted on one day a week (Sunday), valued at selling price."""
from database import db
from helpers import (STOCK_DAY_NAME, BadRequest, check_date, is_stock_day,
                     last_stock_day, num, today)
from catalog import items
from reconcile import reconcile


def check_stock_day(d):
    if d > today():
        raise BadRequest("Stock take date cannot be in the future.")
    if not is_stock_day(d):
        raise BadRequest(
            f"Stock take is done on {STOCK_DAY_NAME}s only. "
            f"The most recent {STOCK_DAY_NAME} is {last_stock_day(d)}.")


def save_stocktake(data):
    d = check_date(data.get("date") or last_stock_day())
    check_stock_day(d)
    prices = {i["item"].lower(): i["sell"] for i in items()}
    rows = []
    for c in data.get("counts", []):
        price = prices.get(str(c["item"]).lower(), 0)
        qty = num(c.get("qty"), f"Count for {c['item']}")
        rows.append((d, c["item"], qty, price, qty * price))
    if not rows:
        raise BadRequest("No items to count. Record goods bought first")
    with db() as con:
        con.execute("DELETE FROM stocktake WHERE date=?", (d,))  # re-saving a day replaces it
        con.executemany("INSERT INTO stocktake(date,item,qty,price,value) VALUES (?,?,?,?,?)", rows)
    return reconcile(d)


def get_stocktake(d):
    """Counts already saved for a day, so the form can be pre-filled."""
    d = check_date(d or last_stock_day())
    with db() as con:
        rows = con.execute("SELECT item, qty FROM stocktake WHERE date=?", (d,)).fetchall()
    return {"date": d, "exists": bool(rows), "counts": {r["item"].lower(): r["qty"] for r in rows}}
