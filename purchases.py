"""Goods bought: item, buying price, selling price, quantity."""
from catalog import canonical_name
from database import db
from helpers import BadRequest, check_date, num, today


def add_purchases(data):
    d = check_date(data.get("date") or today())
    rows = []
    for it in data.get("items", []):
        name = str(it.get("item", "")).strip()
        if not name and not str(it.get("qty", "")).strip():
            continue  # untouched blank row
        if not name:
            raise BadRequest("Every row needs an item")
        name = canonical_name(name)  # must be an item from your list
        qty = num(it.get("qty"), f"Quantity for {name}", allow_blank=False)
        if qty <= 0:
            raise BadRequest(f"Quantity for {name} must be more than 0")
        rows.append((d, name, num(it.get("buy"), f"Buying price for {name}"),
                     num(it.get("sell"), f"Selling price for {name}"), qty))
    if not rows:
        raise BadRequest("Add at least one item with a quantity")
    with db() as con:
        con.executemany("INSERT INTO purchases(date,item,buy,sell,qty) VALUES (?,?,?,?,?)", rows)
    return {"saved": len(rows), "total_cost": sum(r[2] * r[4] for r in rows)}


def delete_purchase(pid):
    with db() as con:
        con.execute("DELETE FROM purchases WHERE id=?", (pid,))
    return {"deleted": pid}


def recent_purchases(limit=40):
    with db() as con:
        rows = con.execute(
            "SELECT id,date,item,buy,sell,qty,buy*qty AS cost,sell*qty AS sell_value "
            "FROM purchases ORDER BY date DESC, id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]
