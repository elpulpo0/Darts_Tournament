from sqlalchemy import inspect, Column, Integer
from modules.database.session import create_session, UsersBase

TEST_DB_URL = "sqlite:///:memory:"

def test_create_session_returns_engine_and_session():
    engine, SessionLocal = create_session(TEST_DB_URL)
    assert engine is not None
    assert SessionLocal is not None

def test_engine_url_matches():
    engine, _ = create_session(TEST_DB_URL)
    url = str(engine.url)
    assert TEST_DB_URL in url or url.startswith("sqlite://")

def test_session_can_open_and_close():
    _, SessionLocal = create_session(TEST_DB_URL)
    session = SessionLocal()
    assert session is not None
    session.close()

def test_can_create_tables():
    engine, _ = create_session(TEST_DB_URL)
    class TempTable(UsersBase):
        __tablename__ = "temp_table"
        id = Column(Integer, primary_key=True)

    UsersBase.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "temp_table" in tables
