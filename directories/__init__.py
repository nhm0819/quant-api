import os
from pathlib import Path

root = Path(os.path.dirname(__file__)).parent

home = root.joinpath("quant_api")

static = home.joinpath("static")

logging = root.joinpath("logging.yaml")

sqlite3 = root.joinpath("sqlite3.db")

market = root.joinpath("market")
