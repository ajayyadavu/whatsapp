# 🔐 Authentication Setup Guide

## Prerequisites
- PostgreSQL installed and running
- Python 3.8+

## Step 1: Install Dependencies

```bash
# Navigate to app directory
cd app

# Install required packages
pip install -r requirements.txt
```

## Step 2: PostgreSQL Setup

### For Windows (using pgAdmin):
1. Open pgAdmin 4
2. Right-click on "Servers" → Create → Server
3. Name: `Local PostgreSQL`
4. Connection tab:
   - Host: `localhost`
   - Port: `5432`
   - Maintenance database: `postgres`
   - Username: `postgres`
   - Password: `postgres`
5. Click "Save"

6. Create a new database:
   - Right-click on "Databases" → Create → Database
   - Database name: `workbench`
   - Owner: `postgres`
   - Click "Save"

### Verify Connection:
```bash
# Test connection from command line
psql -U postgres -h localhost -d workbench
```

## Step 3: Configure Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/workbench

# JWT Settings
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Other existing settings
OLLAMA_URL=http://localhost:11434
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Step 4: Initialize Database

```bash
# From the app directory or root, run:
python -m app.db.init_db

# Or import in your app startup (already done in main.py)
```

## Step 5: Run the Application

```bash
# From root directory
uvicorn app.main:app --reload

# Access the API at http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

## Step 6: Access Login Page

1. Open your frontend HTML file in browser:
   - File: `frontend/login.html`
   - Or serve from a local server

2. Test endpoints:
   - **Register**: POST `/api/v1/auth/register`
   - **Login**: POST `/api/v1/auth/login`
   - **Get User**: GET `/api/v1/auth/me`

## API Endpoints

### Register
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "is_active": 1,
    "created_at": "2024-03-27T10:00:00"
  }
}
```

## Troubleshooting

### Database Connection Error
- Ensure PostgreSQL is running
- Check username/password in `.env`
- Verify port 5432 is accessible

### Module Not Found Errors
- Run: `pip install -r requirements.txt`
- Restart your Python environment

### CORS Issues
- Update `origins` list in `app/main.py` with your frontend URL

## File Structure
```
workbench/
├── app/
│   ├── api/v1/endpoints/auth.py       # Authentication endpoints ✅ NEW
│   ├── core/
│   │   ├── config.py                  # Database config ✅ UPDATED
│   │   └── security.py                # JWT & Password hashing ✅ NEW
│   ├── db/
│   │   ├── base.py                    # SQLAlchemy Base ✅ NEW
│   │   ├── session.py                 # DB session setup ✅ NEW
│   │   └── init_db.py                 # DB initialization ✅ NEW
│   ├── models/
│   │   └── user.py                    # User model ✅ NEW
│   ├── schemas/
│   │   └── user.py                    # Pydantic schemas ✅ NEW
│   ├── services/
│   │   └── user_service.py            # User service ✅ NEW
│   └── main.py                        # FastAPI app ✅ UPDATED
├── frontend/
│   ├── login.html                     # Login page ✅ NEW
│   ├── login.js                       # Login logic ✅ NEW
│   └── index.html                     # Chat app
└── requirements.txt                   # Dependencies ✅ UPDATED
```

## Security Notes
- Change `SECRET_KEY` in production
- Use environment variables for sensitive data
- Implement HTTPS in production
- Consider using stronger password hashing (bcrypt is default)
- Add rate limiting for auth endpoints

## Next Steps
1. Test login/registration in the UI
2. Integrate authentication with your chat endpoints
3. Add role-based access control if needed
4. Implement token refresh mechanism
5. Add forgot password functionality
