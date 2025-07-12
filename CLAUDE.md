# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend Development
```bash
# Install dependencies using uv
uv sync

# Start backend server (development)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start backend server (production)
uvicorn main:app --host 0.0.0.0 --port 8000

# Database migrations
alembic upgrade head                    # Apply migrations
alembic revision --autogenerate -m "message"  # Create new migration

# Run tests
pytest                                  # Run all tests
pytest tests/test_auth.py              # Run specific test file
pytest --cov=. --cov-report=html      # Run with coverage report

# LangGraph CLI (for AI agent development)
langgraph dev --port 2024             # Start LangGraph development server
```

### Frontend Development (Flutter)
```bash
# Navigate to Flutter project
cd frontend_flutter

# Install dependencies
flutter pub get

# Run code generation
flutter packages pub run build_runner build --delete-conflicting-outputs

# Run app
flutter run                            # Run on connected device
flutter run -d chrome                 # Run on web browser
flutter run -d windows                # Run on Windows desktop

# Build
flutter build apk                      # Build Android APK
flutter build ios                     # Build iOS app
flutter build web                     # Build web app

# Run tests
flutter test                          # Run all tests
flutter test test/widget_test.dart    # Run specific test
```

### Docker & Infrastructure
```bash
# Full stack development
docker-compose up -d                  # Start all services
docker-compose up -d postgres redis minio  # Start only data services
docker-compose down                   # Stop all services
docker-compose logs -f dietai-backend # View backend logs

# Database operations
docker-compose exec postgres psql -U dietai -d dietai_db  # Connect to database
```

## High-Level Architecture

### System Overview
DietAI is an AI-powered diet and nutrition management system with the following key components:

1. **AI Agent System** (LangGraph-based)
   - Multi-step food image analysis workflow
   - Nutrition extraction and health advice generation
   - Stateful conversation management
   - Located in `agent/` directory

2. **FastAPI Backend** 
   - RESTful API with comprehensive food, user, and health endpoints
   - JWT-based authentication system
   - PostgreSQL for persistent data, Redis for caching
   - MinIO for file storage
   - Main entry point: `main.py`

3. **Flutter Mobile App**
   - Cross-platform mobile application
   - Riverpod for state management, Go Router for navigation
   - Camera integration for food image capture
   - Located in `frontend_flutter/`

### Core Data Flow
1. **Image Analysis**: User uploads food image → MinIO storage → LangGraph agent processes image → nutrition data extracted → stored in PostgreSQL
2. **Conversation**: User messages → conversation router → AI agent → contextualized responses with nutrition advice
3. **Data Aggregation**: Daily nutrition summaries calculated from individual food records, cached in Redis

### AI Agent Architecture (`agent/agent.py`)
The nutrition agent follows a linear workflow:
- `state_init` → `analyze_image` → `extract_nutrition` → `generate_advice` → `format_response`
- Uses configurable vision and analysis models (OpenAI GPT-4, o3-mini)
- Manages state through LangGraph's StateGraph system

### Key Backend Components
- **Routers**: Organized by feature (`auth_router.py`, `food_router.py`, `health_router.py`, etc.)
- **Models**: SQLAlchemy models in `shared/models/` (user, food, conversation tables)
- **Configuration**: Centralized settings in `shared/config/settings.py` with environment variable support
- **Authentication**: JWT tokens with refresh mechanism in `shared/utils/auth.py`

### Database Schema
- **Users**: Basic user info, preferences, health goals
- **FoodRecords**: Individual food entries with meal type, images, analysis status
- **NutritionDetail**: Detailed nutrition breakdown linked to food records
- **DailyNutritionSummary**: Aggregated daily nutrition data for reporting
- **Conversations**: Chat history for AI assistant interactions

### Frontend Architecture (Flutter)
- **Feature-based structure**: Each major feature (auth, camera, health, etc.) has its own directory
- **Shared components**: Common UI elements in `shared/presentation/widgets/`
- **State management**: Riverpod providers for API data and app state
- **Services**: API client (`core/services/api_service.dart`) and food service abstractions

### Configuration & Environment
- Backend configuration via `shared/config/settings.py` with `DIETAI_` prefixed environment variables
- Support for development/production environments
- Database, Redis, MinIO, and CORS settings configurable
- LangGraph agent configuration in `langgraph.json`

### Key Integration Points
- **LangGraph Agent**: Accessed via SDK client at `http://127.0.0.1:2024`
- **MinIO Storage**: Food images stored with user-specific paths (`food_images/{user_id}/`)
- **Redis Caching**: Nutrition summaries and user sessions cached for performance
- **Database**: PostgreSQL as primary datastore with SQLAlchemy ORM

### Testing Strategy
- Backend: pytest with async support and coverage reporting
- Frontend: Flutter's built-in testing framework
- Test files follow naming convention: `test_*.py` for backend, `*_test.dart` for frontend

## Important Notes
- The project uses Python 3.12+ and modern async/await patterns throughout
- All API responses follow a consistent `BaseResponse` schema with success/error handling
- Image processing requires base64 encoding for agent communication
- CORS is configured for local development with multiple frontend ports
- Database migrations are managed through Alembic
- The system supports multiple AI model providers (OpenAI, Anthropic, Qwen) via configuration