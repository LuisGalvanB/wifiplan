"""
Test configuration.

- RF engine and CV pipeline tests: pure Python, no DB, always run.
- API integration tests: require PostgreSQL. Skipped if DATABASE_URL unreachable.
  To run: start postgres first (docker compose up postgres -d), then pytest.

For local unit testing without Docker:
    pytest tests/test_rf_engine.py tests/test_cv_pipeline.py
"""
import os
import uuid
import pytest


# ── Check if Postgres is available ───────────────────────────────────────────
def _postgres_available() -> bool:
    try:
        import psycopg2
        db_url = os.environ.get("DATABASE_URL", "postgresql://wifiplan:wifiplan@localhost:5432/wifiplan")
        # Parse simple connection string
        import re
        m = re.match(r"postgresql://(\w+):(\w+)@([\w.]+):(\d+)/(\w+)", db_url)
        if not m:
            return False
        conn = psycopg2.connect(
            user=m.group(1), password=m.group(2),
            host=m.group(3), port=int(m.group(4)), database=m.group(5),
            connect_timeout=2,
        )
        conn.close()
        return True
    except Exception:
        return False


POSTGRES_AVAILABLE = _postgres_available()
skip_no_postgres = pytest.mark.skipif(
    not POSTGRES_AVAILABLE,
    reason="PostgreSQL not available (run: docker compose up postgres -d)"
)


# ── Postgres fixtures (only when PG is up) ───────────────────────────────────
if POSTGRES_AVAILABLE:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    import app.models  # noqa
    from app.db.base import Base, get_db
    from app.main import app
    from app.core.security import hash_password
    from fastapi.testclient import TestClient

    TEST_DB_URL = os.environ.get(
        "DATABASE_URL",
        "postgresql://wifiplan:wifiplan@localhost:5432/wifiplan"
    ) + "_test"

    @pytest.fixture(scope="function")
    def db():
        engine = create_engine(TEST_DB_URL)
        # Create test DB
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        base_url = TEST_DB_URL.rsplit("_test", 1)[0]
        import re
        m = re.match(r"postgresql://(\w+):(\w+)@([\w.]+):(\d+)/(\w+)", base_url)
        admin_conn = psycopg2.connect(
            user=m.group(1), password=m.group(2),
            host=m.group(3), port=int(m.group(4)), database="postgres",
        )
        admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = admin_conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname='wifiplan_test'")
        if not cur.fetchone():
            cur.execute("CREATE DATABASE wifiplan_test")
        cur.close()
        admin_conn.close()

        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        session = Session()
        try:
            yield session
        finally:
            session.close()
            Base.metadata.drop_all(bind=engine)
            engine.dispose()

    @pytest.fixture(scope="function")
    def client(db):
        def override():
            yield db
        app.dependency_overrides[get_db] = override
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
        app.dependency_overrides.clear()

    @pytest.fixture
    def demo_user(db):
        from app.models.tenant import User, Organization, Membership, MembershipRole
        org = Organization(name="Test Org", slug=f"test-org-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        user = User(
            email=f"test-{uuid.uuid4().hex[:6]}@example.com",
            hashed_password=hash_password("TestPass1!"),
            full_name="Test User",
        )
        db.add(user)
        db.flush()
        db.add(Membership(organization_id=org.id, user_id=user.id, role=MembershipRole.admin))
        db.commit()
        return {"user": user, "org": org}

    @pytest.fixture
    def auth_headers(client, demo_user):
        resp = client.post("/api/v1/auth/login", json={
            "email": demo_user["user"].email,
            "password": "TestPass1!",
        })
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

else:
    # Stub fixtures so test files can be collected without error
    @pytest.fixture
    def db():
        pytest.skip("PostgreSQL not available")

    @pytest.fixture
    def client(db):
        pytest.skip("PostgreSQL not available")

    @pytest.fixture
    def demo_user(db):
        pytest.skip("PostgreSQL not available")

    @pytest.fixture
    def auth_headers(client, demo_user):
        pytest.skip("PostgreSQL not available")
