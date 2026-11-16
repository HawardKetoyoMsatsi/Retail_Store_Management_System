"""The list of items you sell. Purchases and stock counts pick from this list."""
from database import db
from helpers import BadRequest, num


def clean_name(v):
    name = " ".join(str(v or "").split())
    if not name:
        raise BadRequest("Item name is required")
    if len(name) > 80:
        raise BadRequest("Item name is too long (80 characters at most)")
    return name


def canonical_name(name):
    """The item's name exactly as saved in the list, or an error if it isn't there."""
    name = " ".join(str(name or "").split())
    with db() as con:
        r = con.execute("SELECT name FROM catalog WHERE name=? COLLATE NOCASE", (name,)).fetchone()
    if not r:
        raise BadRequest(f"'{name}' is not in your item list. Add it on the Items tab first")
    return r["name"]


def list_catalog():
    with db() as con:
        rows = con.execute("SELECT id,name,buy,sell FROM catalog ORDER BY name COLLATE NOCASE").fetchall()
        out = []
        for r in rows:
            used = con.execute(
                "SELECT COUNT(*) FROM purchases WHERE LOWER(TRIM(item))=LOWER(?)", (r["name"],)).fetchone()[0]
            out.append({**dict(r), "used": used})
    return out


def items():
    """Every item in the list with total bought and the prices to use.
    Prices come from the latest purchase; before the first purchase, from the list."""
    with db() as con:
        rows = con.execute("SELECT id,name,buy,sell FROM catalog ORDER BY name COLLATE NOCASE").fetchall()
        out = []
        for c in rows:
            bought = con.execute(
                "SELECT COALESCE(SUM(qty),0) FROM purchases WHERE LOWER(TRIM(item))=LOWER(?)", (c["name"],)).fetchone()[0]
            last = con.execute(
                "SELECT buy,sell FROM purchases WHERE LOWER(TRIM(item))=LOWER(?) "
                "ORDER BY date DESC, id DESC LIMIT 1", (c["name"],)).fetchone()
            out.append({"id": c["id"], "item": c["name"], "bought": bought,
                        "buy": last["buy"] if last else c["buy"],
                        "sell": last["sell"] if last else c["sell"]})
    return out


def add_item(data):
    name = clean_name(data.get("name"))
    buy, sell = num(data.get("buy"), "Buying price"), num(data.get("sell"), "Selling price")
    with db() as con:
        if con.execute("SELECT 1 FROM catalog WHERE name=? COLLATE NOCASE", (name,)).fetchone():
            raise BadRequest(f"'{name}' is already in your list")
        con.execute("INSERT INTO catalog(name,buy,sell) VALUES (?,?,?)", (name, buy, sell))
    return {"added": name}


def update_item(data):
    iid = int(data.get("id") or 0)
    name = clean_name(data.get("name"))
    buy, sell = num(data.get("buy"), "Buying price"), num(data.get("sell"), "Selling price")
    with db() as con:
        old = con.execute("SELECT name FROM catalog WHERE id=?", (iid,)).fetchone()
        if not old:
            raise BadRequest("Item not found")
        clash = con.execute("SELECT 1 FROM catalog WHERE name=? COLLATE NOCASE AND id<>?", (name, iid)).fetchone()
        if clash:
            raise BadRequest(f"'{name}' is already in your list")
        con.execute("UPDATE catalog SET name=?, buy=?, sell=? WHERE id=?", (name, buy, sell, iid))
        if name != old["name"]:  # a rename carries through to past records
            con.execute("UPDATE purchases SET item=? WHERE LOWER(TRIM(item))=LOWER(?)", (name, old["name"]))
            con.execute("UPDATE stocktake SET item=? WHERE LOWER(TRIM(item))=LOWER(?)", (name, old["name"]))
    return {"updated": name}


def delete_item(iid):
    with db() as con:
        row = con.execute("SELECT name FROM catalog WHERE id=?", (iid,)).fetchone()
        if not row:
            raise BadRequest("Item not found")
        used = con.execute(
            "SELECT COUNT(*) FROM purchases WHERE LOWER(TRIM(item))=LOWER(?)", (row["name"],)).fetchone()[0]
        if used:
            raise BadRequest(f"'{row['name']}' has {used} purchase record(s), so it can't be deleted")
        con.execute("DELETE FROM catalog WHERE id=?", (iid,))
    return {"deleted": iid}
