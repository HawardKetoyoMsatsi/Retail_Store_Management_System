"""The balance check.

Selling value of goods bought = stock value (at selling price) + sales money
Sales money = money available (cash+pochi+mpesa) + money used for goods
              + money drawn - opening capital
"""
from database import db
from helpers import check_date
from settings import get_capital


def reconcile(d):
    d = check_date(d)
    with db() as con:
        total_selling, total_cost = con.execute(
            "SELECT COALESCE(SUM(sell*qty),0), COALESCE(SUM(buy*qty),0) FROM purchases WHERE date<=?", (d,)).fetchone()
        stock_value, lines = con.execute(
            "SELECT COALESCE(SUM(value),0), COUNT(*) FROM stocktake WHERE date=?", (d,)).fetchone()
        spent, drawn = con.execute(
            "SELECT COALESCE(SUM(spent),0), COALESCE(SUM(drawn),0) FROM daily WHERE date<=?", (d,)).fetchone()
        latest = con.execute(
            "SELECT date, cash+pochi+mpesa AS total FROM daily WHERE date<=? ORDER BY date DESC LIMIT 1", (d,)).fetchone()
        capital = get_capital(con)
    available = latest["total"] if latest else 0
    sales_money = available + spent + drawn - capital
    accounted = stock_value + sales_money
    diff = accounted - total_selling
    return {
        "date": d, "stock_taken": lines > 0, "total_cost": total_cost, "total_selling": total_selling,
        "stock_value": stock_value, "available": available, "available_as_of": latest["date"] if latest else "",
        "spent": spent, "drawn": drawn, "capital": capital, "sales_money": sales_money,
        "accounted": accounted, "difference": diff, "balanced": lines > 0 and abs(diff) < 0.5,
    }
