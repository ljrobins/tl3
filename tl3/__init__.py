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
DB_PATH = os.environ['TL3_DB_PATH']

os.environ['TL3_TXT_DIR'] = os.path.join(os.environ['TL3_DIR'], 'txt')

if not os.path.exists(os.path.split(os.environ['TL3_SECRETS_CACHE'])[0]):
    os.mkdir(os.path.split(os.environ['TL3_SECRETS_CACHE'])[0])

if not os.path.exists(os.path.split(os.environ['TL3_DB_PATH'])[0]):
    os.mkdir(os.path.split(os.environ['TL3_DB_PATH'])[0])

if not os.path.exists(os.environ['TL3_TXT_DIR']):
    os.mkdir(os.environ['TL3_TXT_DIR'])

from .query import *
from .database import *

from .query import _load_secrets

_load_secrets()
