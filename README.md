# Task Manager 

A full-stack task management web application built with **FastAPI** (backend) and **React** (frontend).

### Backend (`backend/.env`)
```
DATABASE_URL=sqlite:///./taskmanager.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Frontend (`frontend/.env`)
```
REACT_APP_API_URL=http://localhost:8000
```
# Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate 
pip install -r requirements.txt
cp .env.example .env    
uvicorn app.main:app --reload
```

API runs at: http://localhost:8000  
Docs at: http://localhost:8000/docs

### Frontend
```bash
cd frontend
cp .env.example .env
npm install
npm start
```

Frontend runs at: http://localhost:3000
---

## Run Tests
```bash
cd backend
pytest tests/ -v
```

## Deployment

- Backend: [Render](https://render.com) — set env vars in dashboard, use `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Frontend: [Vercel](https://vercel.com) — set `REACT_APP_API_URL` to your backend URL

Live demo: _Add your link here_
