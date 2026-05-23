# FastAPI Blog Posting Website

A modern Blog Posting REST API built using FastAPI, PostgreSQL, and SQLAlchemy.

## 🚀 Features

- User Authentication (JWT)
- Create, Read, Update, Delete Blogs
- PostgreSQL Database Integration
- SQLAlchemy ORM
- Password Hashing
- RESTful APIs
- Pydantic Validation
- Virtual Environment Support
- Requirements.txt Support

---

# 🛠 Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Uvicorn
- Pydantic
- Passlib
- JWT Authentication

---

# 📂 Project Structure

```bash
fastapi_blog/
│
├── app/
│   ├── routers/
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   ├── oauth2/
│   ├── utils/
│   └── main.py
│
├── requirements.txt
├── .env
└── README.md
```

---

# ⚙️ Setup Instructions

## 1️⃣ Clone Repository

```bash
git clone <your_repo_url>
cd fastapi_blog
```

---

# 🐍 Create Virtual Environment

## Windows

```bash
python -m venv venv
```

Activate venv:

```bash
venv\Scripts\activate
```

---

## Linux / Mac

```bash
python3 -m venv venv
```

Activate venv:

```bash
source venv/bin/activate
```

---

# 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🐘 PostgreSQL Setup

## Create Database

Open PostgreSQL and create database:

```sql
CREATE DATABASE fastapi_blog;
```

---

# 🔑 Configure Environment Variables

Create a `.env` file in root directory:

```env
DATABASE_HOSTNAME=localhost
DATABASE_PORT=5432
DATABASE_PASSWORD=your_password
DATABASE_NAME=fastapi_blog
DATABASE_USERNAME=postgres

SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

# ▶️ Run FastAPI Server

```bash
uvicorn app.main:app --reload
```

Server will run on:

```bash
http://127.0.0.1:8000
```

---

# 📘 API Documentation

Swagger UI:

```bash
http://127.0.0.1:8000/docs
```

Redoc:

```bash
http://127.0.0.1:8000/redoc
```

---

# 🧪 Example API Endpoints

## Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /login | User Login |

---

## Posts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /posts | Get All Posts |
| GET | /posts/{id} | Get Single Post |
| POST | /posts | Create Post |
| PUT | /posts/{id} | Update Post |
| DELETE | /posts/{id} | Delete Post |

---

# 📜 requirements.txt

Example:

```txt
fastapi
uvicorn
sqlalchemy
psycopg2
python-jose
passlib[bcrypt]
python-multipart
python-dotenv
alembic
```

---

# 👨‍💻 Author

Shahzaib  
AI/ML Engineer | Data Science Student
