import os
import shutil
import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db import get_db
from backend.app.main import app
from backend.app.models import Base


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    # temp DIRECTORY (not bare file): Windows keeps SQLite handles open briefly,
    # so a bare os.unlink at teardown hits WinError 32. dispose() + rmtree with
    # ignore_errors makes teardown deterministic.
    tmp_dir = tempfile.mkdtemp(prefix="week7_test_")
    db_path = os.path.join(tmp_dir, "test_app.db")

    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.pop(get_db, None)
    engine.dispose()
    shutil.rmtree(tmp_dir, ignore_errors=True)
