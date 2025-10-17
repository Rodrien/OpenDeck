# OpenDeck Backend Architecture

**Version:** 1.0
**Date:** October 2025
**Status:** Planning Phase

## Executive Summary

OpenDeck backend is designed for **dual deployment**: on-premises (Docker containers) and cloud (AWS Lambda). The architecture uses FastAPI with a clean separation of concerns, allowing the same codebase to run in both environments with minimal configuration changes.

---

## Architecture Principles

### 1. Separation of Concerns (Clean/Hexagonal Architecture)
- **Core business logic**: Pure Python modules with no framework dependencies
- **Adapters**: HTTP (FastAPI), Lambda (Mangum), CLI, Background workers
- **Single source of truth**: All adapters call the same internal packages

### 2. 12-Factor App Methodology
- Configuration in environment variables
- Logs to stdout (structured JSON)
- Stateless services
- Backing services as attached resources

### 3. Deployment Flexibility
- **On-Premises**: Docker containers with docker-compose
- **Cloud (AWS)**: Lambda functions + DynamoDB + S3
- **Single codebase**: Environment variable switches between modes

---

## Technology Stack

### Core Framework
- **Web Framework**: FastAPI (ASGI) - fast, modern, excellent typing
- **ASGI Server**: Uvicorn (with Gunicorn workers for production)
- **Lambda Adapter**: Mangum - wraps ASGI apps for API Gateway

### Data Storage
- **On-Premises**: PostgreSQL with SQLAlchemy + Alembic migrations
- **Cloud (AWS)**: DynamoDB (serverless, pay-per-request)
- **File Storage**: Local filesystem (on-prem) / S3 (cloud)

### Background Processing
- **On-Premises**: Celery + Redis/RabbitMQ
- **Cloud**: SQS + Lambda or SNS/EventBridge

### AI Integration
- **Primary**: OpenAI API or Claude API (Anthropic)
- **Document Processing**: PyPDF2, python-docx for text extraction
- **Future**: Amazon Bedrock for cost optimization

### Authentication & Security
- **Auth**: JWT tokens with OAuth2
- **Secrets**: HashiCorp Vault (on-prem) / AWS Secrets Manager (cloud)
- **Identity**: Keycloak (on-prem) / Amazon Cognito (cloud)

### Observability
- **Logging**: Structured JSON logs
- **Tracing**: OpenTelemetry
- **Metrics**: Prometheus + Grafana (on-prem) / CloudWatch (AWS)
- **Monitoring**: CloudWatch Logs, X-Ray for AWS

### CI/CD & Infrastructure
- **CI/CD**: GitHub Actions
- **IaC**: Terraform (AWS resources)
- **Containerization**: Docker, docker-compose
- **Registry**: Amazon ECR

---

## Project Structure

```
opendeck-backend/
├── app/
│   ├── core/                      # Business logic (framework-agnostic)
│   │   ├── models.py              # Domain models (Deck, Card, Document, User)
│   │   ├── interfaces.py          # Abstract repository interfaces
│   │   └── services.py            # Business logic layer
│   ├── api/                       # FastAPI routes (HTTP adapter)
│   │   ├── __init__.py
│   │   ├── auth.py                # Authentication endpoints
│   │   ├── decks.py               # Deck CRUD operations
│   │   ├── cards.py               # Flashcard CRUD operations
│   │   ├── documents.py           # Document upload & processing
│   │   └── health.py              # Health check endpoint
│   ├── db/                        # Data access layer
│   │   ├── postgres_repo.py       # PostgreSQL implementation (SQLAlchemy)
│   │   └── dynamo_repo.py         # DynamoDB implementation (boto3/pynamodb)
│   ├── services/                  # Application services
│   │   ├── ai_service.py          # AI flashcard generation
│   │   ├── document_processor.py  # Document text extraction
│   │   ├── storage_service.py     # S3/local file operations
│   │   └── auth_service.py        # Authentication logic
│   ├── workers/                   # Background task workers
│   │   └── tasks.py               # Celery tasks (on-prem only)
│   ├── schemas/                   # Pydantic schemas (request/response models)
│   │   ├── deck.py
│   │   ├── card.py
│   │   ├── document.py
│   │   └── user.py
│   ├── config.py                  # Configuration loader (12-factor)
│   ├── main.py                    # FastAPI app initialization
│   └── lambda_handler.py          # Mangum adapter for Lambda
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── infra/
│   ├── terraform/                 # AWS infrastructure as code
│   │   ├── main.tf
│   │   ├── lambda.tf
│   │   ├── dynamodb.tf
│   │   ├── api_gateway.tf
│   │   └── iam.tf
│   └── docker/
│       └── docker-compose.yml     # On-prem setup
├── alembic/                       # Database migrations (PostgreSQL)
│   ├── versions/
│   └── env.py
├── Dockerfile                     # Multi-stage Docker build
├── docker-compose.yml             # Local development
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Poetry/project metadata
├── .env.example                   # Example environment variables
└── README.md
```

---

## Data Model

### DynamoDB Schema (Cloud)

#### Users Table
```
PK: USER#<user_id>
SK: USER#<user_id>
Attributes:
  - email: string
  - name: string
  - password_hash: string
  - created_at: timestamp
  - updated_at: timestamp
```

#### Decks Table
```
PK: USER#<user_id>
SK: DECK#<deck_id>
Attributes:
  - title: string
  - description: string
  - category: string
  - difficulty: enum (Beginner, Intermediate, Advanced)
  - card_count: number
  - created_at: timestamp
  - updated_at: timestamp
```

#### Flashcards Table
```
PK: DECK#<deck_id>
SK: CARD#<card_id>
Attributes:
  - question: string
  - answer: string
  - source: string (REQUIRED - document name, page, section)
  - source_url: string (optional)
  - created_at: timestamp
  - updated_at: timestamp
```

#### Documents Table
```
PK: USER#<user_id>
SK: DOC#<doc_id>
Attributes:
  - filename: string
  - s3_key: string (cloud) / file_path: string (on-prem)
  - status: enum (uploaded, processing, completed, failed)
  - deck_id: string (optional, if converted to deck)
  - processed_at: timestamp
  - error_message: string (if failed)
```

### PostgreSQL Schema (On-Premises)

Similar structure but normalized:
- `users` table
- `decks` table (FK to users)
- `flashcards` table (FK to decks)
- `documents` table (FK to users)

SQLAlchemy models will use proper relationships and foreign keys.

---

## API Endpoints

### Authentication
```
POST   /api/v1/auth/register          # User registration
POST   /api/v1/auth/login             # User login (returns JWT)
POST   /api/v1/auth/refresh           # Refresh JWT token
POST   /api/v1/auth/logout            # Logout (invalidate token)
```

### Decks
```
GET    /api/v1/decks                  # List user's decks (with filters)
GET    /api/v1/decks/{deck_id}        # Get single deck
POST   /api/v1/decks                  # Create new deck
PUT    /api/v1/decks/{deck_id}        # Update deck
DELETE /api/v1/decks/{deck_id}        # Delete deck
```

### Flashcards
```
GET    /api/v1/decks/{deck_id}/cards           # List cards in deck
GET    /api/v1/cards/{card_id}                 # Get single card
POST   /api/v1/decks/{deck_id}/cards           # Create card manually
PUT    /api/v1/cards/{card_id}                 # Update card
DELETE /api/v1/cards/{card_id}                 # Delete card
```

### Documents & AI Processing
```
POST   /api/v1/documents/upload                # Upload document (returns doc_id)
GET    /api/v1/documents/{doc_id}              # Get document metadata
GET    /api/v1/documents/{doc_id}/status       # Check processing status
POST   /api/v1/documents/{doc_id}/generate     # Generate flashcards from document
DELETE /api/v1/documents/{doc_id}              # Delete document
```

### Health & Monitoring
```
GET    /health                         # Health check
GET    /metrics                        # Prometheus metrics (on-prem)
```

---

## Repository Pattern Implementation

### Abstract Interface
```python
# app/core/interfaces.py
from typing import Protocol, List, Optional
from app.core.models import Deck, Card, User, Document

class DeckRepository(Protocol):
    def get(self, deck_id: str, user_id: str) -> Optional[Deck]: ...
    def list(self, user_id: str, filters: dict) -> List[Deck]: ...
    def create(self, deck: Deck) -> Deck: ...
    def update(self, deck: Deck) -> Deck: ...
    def delete(self, deck_id: str, user_id: str) -> None: ...

class CardRepository(Protocol):
    def get(self, card_id: str) -> Optional[Card]: ...
    def list_by_deck(self, deck_id: str) -> List[Card]: ...
    def create(self, card: Card) -> Card: ...
    def update(self, card: Card) -> Card: ...
    def delete(self, card_id: str) -> None: ...
```

### PostgreSQL Implementation
```python
# app/db/postgres_repo.py
from sqlalchemy.orm import Session
from app.core.interfaces import DeckRepository
from app.core.models import Deck

class PostgresDeckRepo(DeckRepository):
    def __init__(self, session: Session):
        self.session = session

    def get(self, deck_id: str, user_id: str) -> Optional[Deck]:
        return self.session.query(Deck)\
            .filter_by(id=deck_id, user_id=user_id)\
            .first()

    # ... other methods
```

### DynamoDB Implementation
```python
# app/db/dynamo_repo.py
import boto3
from app.core.interfaces import DeckRepository
from app.core.models import Deck

class DynamoDeckRepo(DeckRepository):
    def __init__(self, table_name: str):
        self.table = boto3.resource("dynamodb").Table(table_name)

    def get(self, deck_id: str, user_id: str) -> Optional[Deck]:
        resp = self.table.get_item(
            Key={"PK": f"USER#{user_id}", "SK": f"DECK#{deck_id}"}
        )
        item = resp.get("Item")
        return Deck.from_dynamo(item) if item else None

    # ... other methods
```

---

## AI Integration

### Document Processing Flow

1. **Upload Document** → S3 (cloud) or local storage (on-prem)
2. **Extract Text** → PyPDF2 / python-docx
3. **Generate Flashcards** → OpenAI/Claude API call
4. **Parse Response** → Extract questions, answers, sources
5. **Store Flashcards** → DynamoDB/PostgreSQL
6. **Notify User** → WebSocket or polling endpoint

### AI Service Interface
```python
# app/services/ai_service.py
class FlashcardGenerator:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    async def generate_flashcards(
        self,
        text: str,
        document_name: str,
        context: dict
    ) -> List[Card]:
        """
        Generate flashcards from document text using AI.

        CRITICAL: Must include source attribution per CLAUDE.md
        - Document name
        - Page numbers
        - Section references
        """
        prompt = self._build_prompt(text, document_name)
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        return self._parse_flashcards(response, document_name)

    def _build_prompt(self, text: str, doc_name: str) -> str:
        return f"""
        Extract key concepts from the following document and create flashcards.

        IMPORTANT: For each flashcard, you MUST include:
        1. A clear question
        2. A comprehensive answer
        3. Source reference: "{doc_name} - Page X, Section Y"

        Document text:
        {text}

        Format your response as JSON array of flashcards.
        """
```

---

## Deployment Models

### On-Premises Deployment (Docker)

**Architecture:**
- Docker Compose orchestrates services
- PostgreSQL for data
- Redis for Celery task queue
- Nginx reverse proxy (optional)

**docker-compose.yml:**
```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_BACKEND=postgres
      - DATABASE_URL=postgresql://user:pass@db:5432/opendeck
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=opendeck
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  celery_worker:
    build: .
    command: celery -A app.workers.tasks worker --loglevel=info
    environment:
      - DB_BACKEND=postgres
      - DATABASE_URL=postgresql://user:pass@db:5432/opendeck
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  redis_data:
```

### AWS Cloud Deployment (Lambda)

**Architecture:**
- Lambda functions (container images)
- API Gateway for HTTP routing
- DynamoDB for data storage
- S3 for document storage
- SQS for async processing
- CloudWatch for monitoring

**Key AWS Resources:**
```hcl
# infra/terraform/main.tf

# Lambda Function
resource "aws_lambda_function" "api" {
  function_name = "opendeck-api"
  image_uri     = "${aws_ecr_repository.app.repository_url}:latest"
  role          = aws_iam_role.lambda_exec.arn
  timeout       = 30
  memory_size   = 512

  environment {
    variables = {
      DB_BACKEND           = "dynamo"
      DYNAMO_DECKS_TABLE   = aws_dynamodb_table.decks.name
      DYNAMO_CARDS_TABLE   = aws_dynamodb_table.cards.name
      S3_BUCKET            = aws_s3_bucket.documents.id
      OPENAI_API_KEY_ARN   = aws_secretsmanager_secret.openai.arn
    }
  }
}

# DynamoDB Tables
resource "aws_dynamodb_table" "decks" {
  name           = "opendeck-decks"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "PK"
  range_key      = "SK"

  attribute {
    name = "PK"
    type = "S"
  }
  attribute {
    name = "SK"
    type = "S"
  }
}

# S3 Bucket for Documents
resource "aws_s3_bucket" "documents" {
  bucket = "opendeck-documents-${var.environment}"
}

# API Gateway
resource "aws_apigatewayv2_api" "main" {
  name          = "opendeck-api"
  protocol_type = "HTTP"
}
```

---

## Environment Configuration

### Environment Variables

**Common:**
```bash
# Application
ENV=production|development|local
LOG_LEVEL=INFO
SECRET_KEY=<random-secret-key>

# Database Backend Selection
DB_BACKEND=postgres|dynamo
```

**PostgreSQL (On-Prem):**
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/opendeck
```

**DynamoDB (AWS):**
```bash
AWS_REGION=us-east-1
DYNAMO_DECKS_TABLE=opendeck-decks
DYNAMO_CARDS_TABLE=opendeck-cards
DYNAMO_USERS_TABLE=opendeck-users
DYNAMO_DOCS_TABLE=opendeck-documents
```

**AI Services:**
```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
# OR
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

**Storage:**
```bash
# On-Prem
STORAGE_PATH=/var/opendeck/documents

# AWS
S3_BUCKET=opendeck-documents
S3_REGION=us-east-1
```

**Background Processing:**
```bash
# On-Prem
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# AWS
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/.../opendeck-tasks
```

---

## Security Considerations

### Authentication
- JWT tokens with expiration
- Refresh token rotation
- Password hashing with bcrypt
- Rate limiting on auth endpoints

### Data Security
- Secrets in Vault (on-prem) or AWS Secrets Manager (cloud)
- No secrets in code or Docker images
- Encrypt data at rest (DynamoDB encryption, PostgreSQL TDE)
- HTTPS/TLS for all external communication

### IAM & Access Control
- Principle of least privilege
- Lambda execution roles with minimal permissions
- User data isolation (multi-tenancy)
- API Gateway authorization

### Input Validation
- Pydantic schemas for request validation
- File type validation for uploads
- Size limits on document uploads
- SQL injection prevention (parameterized queries)

---

## Performance Considerations

### Lambda Cold Starts
- Use Lambda container images (faster cold starts than ZIP)
- Consider provisioned concurrency for critical paths
- Keep dependencies minimal
- Reuse connections (database, AI API clients)

### Database Optimization
- DynamoDB: Use GSIs for common query patterns
- PostgreSQL: Add indexes on foreign keys and common filters
- Connection pooling (SQLAlchemy)

### Caching
- Redis for session storage (on-prem)
- DynamoDB TTL for temporary data
- Cache AI-generated flashcards to avoid duplicate processing

### Rate Limiting
- API Gateway throttling (cloud)
- FastAPI middleware (on-prem)
- OpenAI API rate limit handling with exponential backoff

---

## Testing Strategy

### Unit Tests
```python
# tests/unit/test_deck_service.py
def test_create_deck():
    repo = MockDeckRepository()
    service = DeckService(repo)
    deck = service.create_deck(user_id="123", data={...})
    assert deck.id is not None
```

### Integration Tests
```python
# tests/integration/test_api.py
def test_create_deck_endpoint(client):
    response = client.post("/api/v1/decks", json={...})
    assert response.status_code == 201
```

### E2E Tests
- Use TestContainers for PostgreSQL/Redis
- Use LocalStack for AWS services (DynamoDB, S3, SQS)
- Mock AI API calls

---

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
name: Build and Deploy

on:
  push:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest --cov

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker image
        run: docker build -t opendeck-backend:${{ github.sha }} .

      - name: Push to ECR
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
          docker tag opendeck-backend:${{ github.sha }} $ECR_REGISTRY/opendeck:latest
          docker push $ECR_REGISTRY/opendeck:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Lambda
        run: |
          cd infra/terraform
          terraform apply -auto-approve
```

---

## Monitoring & Observability

### Logging
```python
# Structured JSON logging
import logging
import json

logger = logging.getLogger(__name__)

def log_event(event_type: str, **kwargs):
    logger.info(json.dumps({
        "event": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }))
```

### Metrics
- Request count, latency, error rates
- Database query performance
- AI API call duration and cost
- Document processing time

### Alerts
- Lambda errors and timeouts
- DynamoDB throttling
- High AI API costs
- Failed document processing

---

## Development Workflow

### Local Development
1. Clone repository
2. Copy `.env.example` to `.env` and configure
3. Run `docker-compose up -d` to start PostgreSQL and Redis
4. Run `pip install -r requirements.txt`
5. Run `alembic upgrade head` to apply migrations
6. Run `uvicorn app.main:app --reload` for development server
7. Access API at `http://localhost:8000`
8. View docs at `http://localhost:8000/docs` (Swagger UI)

### Testing with LocalStack
```bash
# Start LocalStack
docker run -d -p 4566:4566 localstack/localstack

# Configure AWS CLI to use LocalStack
export AWS_ENDPOINT_URL=http://localhost:4566

# Run tests
pytest tests/integration/
```

---

## Migration Path

### Phase 1: MVP with Static Data (Week 1-2)
- [ ] Set up FastAPI project structure
- [ ] Implement auth service with JWT
- [ ] Create CRUD endpoints for decks and cards
- [ ] PostgreSQL setup with SQLAlchemy
- [ ] Docker setup for local development
- [ ] Basic unit tests

### Phase 2: AI Integration (Week 3-4)
- [ ] Document upload endpoint
- [ ] S3/local storage service
- [ ] Text extraction from PDF/DOCX
- [ ] OpenAI/Claude integration
- [ ] Flashcard generation service
- [ ] Source attribution implementation
- [ ] Background processing with Celery

### Phase 3: AWS Deployment (Week 5-6)
- [ ] DynamoDB repository implementation
- [ ] Repository factory pattern
- [ ] Terraform infrastructure setup
- [ ] Lambda container deployment
- [ ] API Gateway configuration
- [ ] SQS for async processing
- [ ] CloudWatch logging and monitoring

### Phase 4: Production Hardening (Week 7-8)
- [ ] Comprehensive error handling
- [ ] Rate limiting
- [ ] Input validation and sanitization
- [ ] Security audit
- [ ] Performance optimization
- [ ] Documentation
- [ ] Load testing
- [ ] Production deployment

---

## Cost Estimates (AWS)

### Monthly Costs (1000 active users)
- **Lambda**: ~$50 (1M requests, 512MB, 5s avg duration)
- **DynamoDB**: ~$25 (on-demand, 10GB storage, 1M reads, 500K writes)
- **S3**: ~$10 (100GB documents)
- **API Gateway**: ~$10 (1M requests)
- **CloudWatch**: ~$10 (logs and metrics)
- **OpenAI API**: ~$100-500 (varies by usage)

**Total**: ~$200-800/month depending on AI usage

---

## References

### Documentation
- [FastAPI](https://fastapi.tiangolo.com/)
- [Mangum](https://mangum.io/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Pynamodb](https://pynamodb.readthedocs.io/)
- [Celery](https://docs.celeryproject.org/)
- [OpenAI API](https://platform.openai.com/docs/)

### AWS Services
- [Lambda](https://docs.aws.amazon.com/lambda/)
- [DynamoDB](https://docs.aws.amazon.com/dynamodb/)
- [API Gateway](https://docs.aws.amazon.com/apigateway/)
- [Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)

---

## Contact & Support

For questions or contributions, please refer to the main repository README or open an issue on GitHub.
