import dotenv
dotenv.load_dotenv('.env.secret')

import os
import inspect

os.environ["TLE_DIR"] = os.path.dirname(
    os.path.abspath(inspect.getsourcefile(lambda: 0))
)

from .query import *
from .database import *
from .scrape import *