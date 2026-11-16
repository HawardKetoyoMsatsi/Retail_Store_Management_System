# Retail Store Manager

A store app that runs on your computer. It needs only Python 3.8 or newer, with nothing to install. Data is stored in a SQLite file, `store.db`, which is created next to `app.py` the first time you run it.

## Run it in VS Code
1. Open the `retail_store` folder in VS Code (File → Open Folder).
2. Open `app.py` and press the ▶ Run button, or run this in the terminal (Ctrl+`):
   ```
   python app.py
   ```
   On Mac or Linux you may need `python3 app.py`.
3. Your browser opens at http://localhost:8000. If it doesn't, open that address yourself.
4. Press Ctrl+C in the terminal to stop it.

To use another port, set `PORT` first (for example `PORT=9000 python app.py`).

## Which file does what (for pasting updates)

| File | What it holds | Update it when you want to change… |
|---|---|---|
| `app.py` | Starts the app | Almost never |
| `config.py` | Port, database location, stock take day | The port, where the data file lives, or the day stock is counted |
| `database.py` | Creates the database tables | Adding a new table or column |
| `helpers.py` | Validation and date helpers | Input rules (for example negative numbers) |
| `catalog.py` | The list of items you sell | How items are added, renamed, deleted or priced |
| `purchases.py` | Goods bought | How purchases are saved or listed |
| `daily.py` | Daily cash / Pochi / M-Pesa records | The daily money record |
| `settings.py` | Opening capital | Business settings |
| `stocktake.py` | Saving a stock take | Stock take behaviour |
| `reconcile.py` | The balance check formula | How "balanced" is worked out |
| `dashboard.py` | Numbers shown on the Dashboard | Adding or changing dashboard figures |
| `server.py` | The list of URLs ("routes") | Connecting a new feature to the page |
| `web/index.html` | The page layout | Tabs, forms, text |
| `web/style.css` | Colours and look | Appearance |
| `web/app.js` | What the buttons and charts do | Page behaviour, charts |

Tips for updating:
- Replace the whole file you are changing, then stop the app (Ctrl+C) and run it again.
- Changes to the `web/` files only need a browser refresh (Ctrl+F5), not a restart.
- A new feature usually touches three places: a function in one of the Python files, a line in `server.py`, and the page in `web/`.
- Back up `store.db` before big changes.

## Using it (start with the Items tab)
- **Dashboard:** the balance check, money now, expected profit, charts, stock on the shelf and recent records. Set your opening capital at the bottom.
- **Items:** your list of everything you sell, with a usual buying and selling price. Add items here first. You can rename an item (past records follow the new name) or change its prices. An item that already has purchases can't be deleted.
- **Goods Bought:** pick each item from a dropdown (its usual prices fill in and can be changed), then enter the quantity. Only items from your list are accepted. You can delete a mistaken row.
- **Daily Money:** cash, Pochi, M-Pesa, money used to buy goods and money drawn. "Used to buy goods" is pre-filled from that day's purchases. Saving the same date again updates it.
- **Sunday Stock Take:** every item in your list appears, so you count each one. Stock is valued at the latest selling price. Stock is counted on Sundays only: the app rejects any other date, never accepts a future date, and defaults to the most recent Sunday. If you reopen a Sunday that is already saved, the counts are filled in, and saving again replaces them. The Dashboard shows a reminder: done, due today, overdue, or when the next one is.
  To count on a different day, change `STOCK_TAKE_WEEKDAY` in `config.py` (Monday = 0 … Sunday = 6), then restart.

## The balance check
Selling value of goods bought = stock value (at selling price) + sales money

Sales money = money available (cash + Pochi + M-Pesa) + money used to buy goods + money drawn − opening capital

Enter your opening capital once. If you started with goods already in stock, record them as a purchase. Enter every day's money record, because a missing day shows up as a shortage.

## Backup
Copy `store.db` to back up all your data. To start fresh, stop the app and delete `store.db`.
