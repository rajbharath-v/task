import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=engine)
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def register_and_login():
    client.post("/register", json={"username": "testuser", "email": "test@test.com", "password": "password123"})
    resp = client.post("/login", json={"username": "testuser", "password": "password123"})
    token = resp.json().get("access_token")
    assert token is not None, f"Login failed: {resp.json()}"
    return token


def test_register():
    resp = client.post("/register", json={"username": "user1", "email": "user1@test.com", "password": "pass123"})
    assert resp.status_code == 201
    assert resp.json()["username"] == "user1"


def test_register_duplicate_username():
    # FIX 1: FastAPI returns 400 for duplicate (our router raises HTTPException 400)
    # First registration
    client.post("/register", json={"username": "user1", "email": "a@test.com", "password": "pass123"})
    # Second registration with same username
    resp = client.post("/register", json={"username": "user1", "email": "b@test.com", "password": "pass123"})
    assert resp.status_code == 400  # our router returns 400 for duplicate username


def test_login():
    client.post("/register", json={"username": "user1", "email": "user1@test.com", "password": "pass123"})
    resp = client.post("/login", json={"username": "user1", "password": "pass123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password():
    client.post("/register", json={"username": "user1", "email": "user1@test.com", "password": "pass123"})
    resp = client.post("/login", json={"username": "user1", "password": "wrong"})
    assert resp.status_code == 401


def test_create_task():
    token = register_and_login()
    resp = client.post("/tasks", json={"title": "My Task", "description": "desc"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    assert resp.json()["title"] == "My Task"


def test_get_tasks():
    token = register_and_login()
    client.post("/tasks", json={"title": "Task 1"}, headers={"Authorization": f"Bearer {token}"})
    client.post("/tasks", json={"title": "Task 2"}, headers={"Authorization": f"Bearer {token}"})
    resp = client.get("/tasks", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_get_task_by_id():
    token = register_and_login()
    created = client.post("/tasks", json={"title": "Task"}, headers={"Authorization": f"Bearer {token}"}).json()
    resp = client.get(f"/tasks/{created['id']}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_update_task():
    token = register_and_login()
    created = client.post("/tasks", json={"title": "Task"}, headers={"Authorization": f"Bearer {token}"}).json()
    resp = client.put(f"/tasks/{created['id']}", json={"completed": True}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["completed"] is True


def test_delete_task():
    token = register_and_login()
    created = client.post("/tasks", json={"title": "Task"}, headers={"Authorization": f"Bearer {token}"}).json()
    resp = client.delete(f"/tasks/{created['id']}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204


def test_task_filter_completed():
    token = register_and_login()
    t1 = client.post("/tasks", json={"title": "Task 1"}, headers={"Authorization": f"Bearer {token}"}).json()
    client.post("/tasks", json={"title": "Task 2"}, headers={"Authorization": f"Bearer {token}"})
    client.put(f"/tasks/{t1['id']}", json={"completed": True}, headers={"Authorization": f"Bearer {token}"})
    resp = client.get("/tasks?completed=true", headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["total"] == 1


def test_cannot_access_other_users_task():
    # FIX 2: Register user1 and login separately to avoid KeyError
    client.post("/register", json={"username": "testuser", "email": "test@test.com", "password": "password123"})
    resp1 = client.post("/login", json={"username": "testuser", "password": "password123"})
    token1 = resp1.json().get("access_token")
    assert token1 is not None, f"User1 login failed: {resp1.json()}"

    # Create task as user1
    created = client.post("/tasks", json={"title": "Task"}, headers={"Authorization": f"Bearer {token1}"}).json()

    # Register and login as user2
    client.post("/register", json={"username": "user2", "email": "u2@test.com", "password": "pass123"})
    resp2 = client.post("/login", json={"username": "user2", "password": "pass123"})
    token2 = resp2.json().get("access_token")
    assert token2 is not None, f"User2 login failed: {resp2.json()}"

    # User2 tries to access user1's task
    resp = client.get(f"/tasks/{created['id']}", headers={"Authorization": f"Bearer {token2}"})
    assert resp.status_code == 404