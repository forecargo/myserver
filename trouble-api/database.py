import os
import time
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


@contextmanager
def get_session():
    session = Session(engine)
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    for attempt in range(10):
        try:
            Base.metadata.create_all(engine)
            return
        except Exception as e:
            if attempt == 9:
                raise
            time.sleep(3)
