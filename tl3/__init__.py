import os
import inspect

os.environ['TL3_DIR'] = os.path.dirname(
    os.path.abspath(inspect.getsourcefile(lambda: 0))
)
os.environ['TL3_SECRETS_CACHE'] = os.path.join(
    os.environ['TL3_DIR'], 'resources', '.env.secret'
)
os.environ['TL3_DB_PATH'] = os.path.join(
    os.environ['TL3_DIR'], 'processed', 'twoline.parquet'
)
os.environ['TL3_TXT_DIR'] = os.path.join(os.environ['TL3_DIR'], 'txt')

from .query import *
from .database import *
from .scrape import *

load_secrets()
