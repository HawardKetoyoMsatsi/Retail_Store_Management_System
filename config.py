"""Settings: where the data lives, which port the app uses, and the stock take day."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(HERE, "web")
DB_PATH = os.environ.get("STORE_DB", os.path.join(HERE, "store.db"))
PORT = int(os.environ.get("PORT", "8000"))

# The one day of the week when stock is counted.
# Monday = 0, Tuesday = 1, ... Saturday = 5, Sunday = 6
STOCK_TAKE_WEEKDAY = 6
