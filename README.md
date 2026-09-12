# AI² — Privacy-First Network of Personal AI Agents

A hackathon project demonstrating secure agent-to-agent communication with granular privacy controls and permission management.

## Project Overview

Users have Personal AI Agents that can communicate securely while protecting private data. Each agent operates within its own user's permission scope, and all cross-agent data access is mediated by a server-side permission engine.

### Core Security Principle
**Agent A must NEVER directly access User B's database.**

All cross-user data flows through:
1. Permission Engine (checks authorization)
2. Data Access Layer (filters fields)
3. Communication Server (routes messages)

## Tech Stack

- **Frontend**: React + Vite
- **Backend**: Python + FastAPI
- **Database**: SQLite
- **Authentication**: JWT tokens
- **API Communication**: REST

## Project Structure

```
byte/
├── backend/               # FastAPI server
│   ├── app/
│   │   ├── main.py       # Entry point
│   │   ├── config.py     # Configuration
│   │   ├── models/       # Data models
│   │   ├── database/     # SQLite setup
│   │   ├── api/          # API endpoints
│   │   └── services/     # Business logic
│   ├── requirements.txt
│   └── .env.example
├── frontend/              # React + Vite app
│   ├── src/
│   └── package.json
└── docker-compose.yml     # Optional: containerization
```

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 16+
- SQLite3

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Create Environment File

```bash
cd backend
cp .env.example .env
```

Edit `.env` with your settings:
```
DATABASE_URL=sqlite:///./byte.db
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Initialize Database

```bash
cd backend
python -c "from app.database.db import init_db; init_db()"
```

### Run Backend Server

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at: `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: `http://localhost:5173`

## API Endpoints (Phase 2)

### Authentication
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login user

### User Data
- `GET /api/users/me` - Get current user info
- `GET /api/users/me/agent` - Get user's agent
- `GET /api/users/me/calendar` - Get user's calendar
- `GET /api/users/me/preferences` - Get user's preferences
- `GET /api/users/me/location` - Get user's current location
- `GET /api/users/me/budget` - Get user's budget info

### Agent Health
- `GET /api/health` - Server health check
- `GET /api/agents/status` - Agent status

## Phase 2 Implementation

This release includes:

✅ FastAPI backend foundation  
✅ SQLite database with schema  
✅ User A and User B with mock data  
✅ Agent A and Agent B definitions  
✅ Isolated data access (users can only read their own data)  
✅ JWT authentication  
✅ Basic API endpoints  
✅ Permission engine foundation (ready for Phase 4)  
✅ Database seeding with realistic test data  

## Next Phases

- **Phase 3**: Real Agent-to-Agent Communication
- **Phase 4**: Server-Side Permission Engine
- **Phase 5**: Granular Permission Controls
- **Phase 6**: Consent Screens
- **Phase 7**: Data Minimization
- **Phase 8**: Expiration & Revocation
- **Phase 9**: Audit Logging
- **Phase 10+**: Demo Scenarios & LLM Integration

## Development Notes

### Database
The SQLite database is created automatically on first run. Each user has isolated data:
- User A (user_id=1) with Agent A
- User B (user_id=2) with Agent B

### Testing the Backend

```bash
# Test User A authentication
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'

# Get User A's calendar (with token)
curl -X GET http://localhost:8000/api/users/me/calendar \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Default Test Credentials

- **User A**: username=`alice`, password=`password123`
- **User B**: username=`bob`, password=`password123`

## Security Notes

- Never commit `.env` file with real secrets
- JWT tokens expire after 30 minutes by default
- All cross-user data requests will be validated by permission engine (Phase 4)
- Current phase does NOT implement inter-agent communication yet
- Current phase enforces isolation at data access layer level

## License

MIT

## Contact

For questions about this project, please open an issue on GitHub.
