# Chatwise AI Sales Agent

AI Sales Agent with RAG capabilities and human handover, built on the Chatwise platform.

## Features

- 🤖 AI-powered sales agent using GPT-4
- 📚 RAG-based knowledge retrieval using pgvector
- 🔄 Real-time chat with Supabase Realtime
- 👋 Intelligent human handover based on confidence scoring
- 📝 Knowledge base management for training the bot
- 🔒 Integration with existing Supabase auth system

## Tech Stack

- **FastAPI**: Modern, fast API framework
- **Supabase**: Database, auth, and real-time capabilities
- **pgvector**: Vector storage for embeddings
- **OpenAI API**: GPT-4 for LLM responses and text-embedding-3-large for embeddings
- **LangChain**: RAG orchestration
- **Pydantic**: Data validation with version 2.x
- **Docker**: Containerization using Alpine-based Python 3.11
- **GitHub Actions**: CI/CD pipeline
- **Render**: Deployment platform

## Setup & Installation

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Supabase account with pgvector extension enabled
- OpenAI API key

### Environment Variables

Create a `.env` file in the root directory based on `.env.example`:

```
# Supabase Configuration
SUPABASE_URL=https://your-supabase-url.supabase.co
SUPABASE_KEY=your-supabase-service-key
SUPABASE_ANON_KEY=your-supabase-anon-key

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Application Settings
APP_ENVIRONMENT=development
LOG_LEVEL=INFO

# File Upload Settings
MAX_UPLOAD_SIZE_MB=10
ALLOWED_EXTENSIONS=pdf

# RAG Settings
MAX_CHUNK_SIZE=1000
DEFAULT_RETRIEVAL_COUNT=5
DEFAULT_HANDOVER_THRESHOLD=0.7
```

### Database Setup

Run the migration script to set up the database schema:

```bash
cat migrations/initial_schema.sql | psql -h your-supabase-host -U postgres
```

Alternatively, you can run the SQL script from the Supabase SQL Editor.

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

3. Or with Docker Compose:
   ```bash
   docker-compose up
   ```

## API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Key Endpoints

### Knowledge Base Management

- `POST /api/knowledge-base/create`: Create a new knowledge base
- `GET /api/knowledge-base/list/{bot_id}`: List all knowledge bases for a bot
- `POST /api/knowledge-base/documents/upload`: Upload a document (PDF)
- `POST /api/knowledge-base/documents/webpage`: Process webpage data
- `GET /api/knowledge-base/documents/{knowledge_base_id}`: List documents in a knowledge base

### Chat and Conversation

- `POST /api/chat/conversations`: Create a new conversation
- `GET /api/chat/conversations/{bot_id}`: List conversations for a bot
- `GET /api/chat/messages/{conversation_id}`: Get messages in a conversation
- `POST /api/chat/query`: Send a query to the bot
- `POST /api/chat/handover`: Request a handover to a human agent
- `POST /api/chat/assign`: Assign a conversation to an agent
- `POST /api/chat/close`: Close a conversation

### Health Check

- `GET /health`: Check system health and service availability

## Architecture

This AI Sales Agent component integrates with the main Chatwise platform, extending the existing bot system with RAG capabilities and human handover features. It respects the existing tables and user subscription limits while adding specialized functionality.

### Integration Points

1. **Authentication**: Uses existing Supabase JWT authentication
2. **Bot Management**: Works with the existing `bots` table
3. **User Subscriptions**: Respects limits defined in the `user_limits` table
4. **Realtime Chat**: Uses Supabase Realtime for client-server communication

## Deployment

The application is deployed to Render as a Web Service through GitHub Actions CI/CD pipeline. The workflow builds a Docker image and deploys it to Render.

## License

[MIT](LICENSE)