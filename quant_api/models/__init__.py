from __future__ import annotations as __annotations__

from typing import Sequence

from pydantic import BaseModel
from sqlalchemy import Column, select
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import inspect
from sqlalchemy.orm import declarative_base

Base = declarative_base()
