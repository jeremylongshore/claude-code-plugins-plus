---
description: Generate production-ready FastAPI REST API with async and authentication
shortcut: fas
category: backend
difficulty: intermediate
estimated_time: 5-10 minutes
---

# FastAPI Scaffold

Generates a complete FastAPI REST API boilerplate with async support, authentication, database integration, and testing setup.

## What This Command Does

**Generated Project:**
-  FastAPI with Python 3.10+
-  Async/await throughout
-  JWT authentication
-  Database integration (SQLAlchemy async)
-  Pydantic models & validation
-  Automatic OpenAPI docs
-  Testing setup (Pytest + httpx)
-  Docker configuration
-  Example CRUD endpoints

**Output:** Complete API project ready for development

**Time:** 5-10 minutes

---

## Usage

```bash
# Generate full FastAPI API
/fastapi-scaffold "Task Management API"

# Shortcut
/fas "E-commerce API"

# With specific database
/fas "Blog API" --database postgresql

# With authentication type
/fas "Social API" --auth jwt --database postgresql
```

---

## Example Output

**Input:**
```
/fas "Task Management API" --database postgresql
```

**Generated Project Structure:**
```
task-api/
├── app/
│   ├── api/
│   │   ├── deps.py           # Dependencies
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py       # Auth endpoints
│   │       └── tasks.py      # Task endpoints
│   ├── core/
│   │   ├── config.py         # Settings
│   │   ├── security.py       # JWT, password hashing
│   │   └── database.py       # Database connection
│   ├── models/               # SQLAlchemy models
│   │   ├── user.py
│   │   └── task.py
│   ├── schemas/              # Pydantic schemas
│   │   ├── user.py
│   │   └── task.py
│   ├── services/             # Business logic
│   │   ├── auth.py
│   │   └── task.py
│   ├── db/
│   │   └── init_db.py        # Database initialization
│   ├── main.py               # FastAPI app
│   └── __init__.py
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_tasks.py
├── alembic/                  # Database migrations
│   ├── versions/
│   └── env.py
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Generated Files

### 1. **app/main.py** (Application Entry)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1 import auth, tasks
from app.core.config import settings
from app.core.database import engine
from app.models import Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0"
    }

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(tasks.router, prefix=f"{settings.API_V1_STR}/tasks", tags=["tasks"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. **app/core/config.py** (Settings)

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Task API"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    ALLOWED_HOSTS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### 3. **app/core/security.py** (Authentication)

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

### 4. **app/core/database.py** (Database Setup)

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 5. **app/models/user.py** (User Model)

```python
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")
```

### 6. **app/models/task.py** (Task Model)

```python
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="tasks")
```

### 7. **app/schemas/user.py** (Pydantic Schemas)

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class UserInDB(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class User(UserInDB):
    pass

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
```

### 8. **app/schemas/task.py** (Task Schemas)

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class TaskInDB(TaskBase):
    id: str
    completed: bool
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Task(TaskInDB):
    pass
```

### 9. **app/api/deps.py** (Dependencies)

```python
from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import oauth2_scheme, decode_access_token
from app.models.user import User

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    payload = decode_access_token(token)
    email: str = payload.get("sub")

    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

    user = db.query(User).filter(User.email == email).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user
```

### 10. **app/api/v1/tasks.py** (Task Endpoints)

```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.task import Task as TaskModel
from app.schemas.task import Task, TaskCreate, TaskUpdate

router = APIRouter()

@router.get("/", response_model=List[Task])
async def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    tasks = db.query(TaskModel)\
        .filter(TaskModel.user_id == current_user.id)\
        .offset(skip)\
        .limit(limit)\
        .all()
    return tasks

@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = TaskModel(
        **task_in.dict(),
        user_id=current_user.id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(TaskModel)\
        .filter(TaskModel.id == task_id, TaskModel.user_id == current_user.id)\
        .first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return task

@router.patch("/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(TaskModel)\
        .filter(TaskModel.id == task_id, TaskModel.user_id == current_user.id)\
        .first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    for field, value in task_in.dict(exclude_unset=True).items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(TaskModel)\
        .filter(TaskModel.id == task_id, TaskModel.user_id == current_user.id)\
        .first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    db.delete(task)
    db.commit()
```

### 11. **tests/test_tasks.py** (Pytest Tests)

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, test_user_token):
    response = await client.post(
        "/api/v1/tasks/",
        json={
            "title": "Test Task",
            "description": "Test description"
        },
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert "id" in data

@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient, test_user_token):
    response = await client.get(
        "/api/v1/tasks/",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_create_task_unauthorized(client: AsyncClient):
    response = await client.post(
        "/api/v1/tasks/",
        json={"title": "Test"}
    )

    assert response.status_code == 401
```

### 12. **requirements.txt**

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
pydantic==2.5.3
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
alembic==1.13.1
psycopg2-binary==2.9.9

# Development
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
black==23.12.1
isort==5.13.2
mypy==1.8.0
```

---

## Features

**Performance:**
- Async/await for high concurrency
- Background tasks support
- WebSocket support (optional)
- Automatic Pydantic validation

**Documentation:**
- Auto-generated OpenAPI (Swagger)
- ReDoc documentation
- Type hints throughout

**Database:**
- SQLAlchemy ORM with async support
- Alembic migrations
- Connection pooling

**Security:**
- JWT authentication
- Password hashing (bcrypt)
- CORS middleware
- Trusted host middleware

**Testing:**
- Pytest with async support
- Test fixtures
- Coverage reporting

---

## Getting Started

**1. Install dependencies:**
```bash
pip install -r requirements.txt
```

**2. Configure environment:**
```bash
cp .env.example .env
# Edit .env with your database URL and secrets
```

**3. Run database migrations:**
```bash
alembic upgrade head
```

**4. Start development server:**
```bash
uvicorn app.main:app --reload
```

**5. View API docs:**
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

**6. Run tests:**
```bash
pytest
```

---

## Related Commands

- `/express-api-scaffold` - Generate Express.js boilerplate
- Backend Architect (agent) - Architecture review
- API Builder (agent) - API design guidance

---

**Build high-performance APIs. Scale effortlessly. Deploy confidently.** 
