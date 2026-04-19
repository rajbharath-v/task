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
    return resp.json()["access_token"]


def test_register():
    resp = client.post("/register", json={"username": "user1", "email": "user1@test.com", "password": "pass123"})
    assert resp.status_code == 201
    assert resp.json()["username"] == "user1"


def test_register_duplicate_username():
    client.post("/register", json={"username": "user1", "email": "a@test.com", "password": "pass"})
    resp = client.post("/register", json={"username": "user1", "email": "b@test.com", "password": "pass"})
    assert resp.status_code == 400


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
    token1 = register_and_login()
    created = client.post("/tasks", json={"title": "Task"}, headers={"Authorization": f"Bearer {token1}"}).json()
    client.post("/register", json={"username": "user2", "email": "u2@test.com", "password": "pass"})
    resp2 = client.post("/login", json={"username": "user2", "password": "pass"})
    token2 = resp2.json()["access_token"]
    resp = client.get(f"/tasks/{created['id']}", headers={"Authorization": f"Bearer {token2}"})
    assert resp.status_code == 404
