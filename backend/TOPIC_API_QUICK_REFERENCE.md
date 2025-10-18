# Topic API Quick Reference

## Base URL
All endpoints are prefixed with `/api/v1`

## Authentication
All endpoints (except topic listing and retrieval) require Bearer token authentication:
```
Authorization: Bearer <your-jwt-token>
```

---

## Topic Management

### List All Topics
```http
GET /api/v1/topics?limit=100&offset=0
```

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Cellular Biology",
      "description": "Topics related to cell structure and function",
      "created_at": "2025-10-18T12:00:00",
      "updated_at": "2025-10-18T12:00:00"
    }
  ],
  "total": 50,
  "limit": 100,
  "offset": 0
}
```

### Get Single Topic
```http
GET /api/v1/topics/{topic_id}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Cellular Biology",
  "description": "Topics related to cell structure and function",
  "created_at": "2025-10-18T12:00:00",
  "updated_at": "2025-10-18T12:00:00"
}
```

### Create Topic
```http
POST /api/v1/topics
Content-Type: application/json

{
  "name": "Cellular Biology",
  "description": "Topics related to cell structure and function"
}
```

**Response:** 201 Created
```json
{
  "id": "uuid",
  "name": "Cellular Biology",
  "description": "Topics related to cell structure and function",
  "created_at": "2025-10-18T12:00:00",
  "updated_at": "2025-10-18T12:00:00"
}
```

**Errors:**
- `409 Conflict`: Topic with same name already exists

### Update Topic
```http
PUT /api/v1/topics/{topic_id}
Content-Type: application/json

{
  "name": "Advanced Cellular Biology",
  "description": "Updated description"
}
```

**Response:** 200 OK (same structure as create)

**Errors:**
- `404 Not Found`: Topic doesn't exist
- `409 Conflict`: New name conflicts with existing topic

### Delete Topic
```http
DELETE /api/v1/topics/{topic_id}
```

**Response:** 204 No Content

**Note:** This will automatically remove all associations with decks and cards (cascade delete)

---

## Deck-Topic Associations

### Associate Topic with Deck
```http
POST /api/v1/topics/decks/{deck_id}/topics
Content-Type: application/json
Authorization: Bearer <token>

{
  "topic_id": "uuid"
}
```

**Response:** 204 No Content

**Errors:**
- `404 Not Found`: Deck or topic doesn't exist, or no access to deck
- `401 Unauthorized`: Invalid or missing authentication

### Remove Topic from Deck
```http
DELETE /api/v1/topics/decks/{deck_id}/topics/{topic_id}
Authorization: Bearer <token>
```

**Response:** 204 No Content

---

## Card-Topic Associations

### Associate Topic with Card
```http
POST /api/v1/topics/cards/{card_id}/topics
Content-Type: application/json
Authorization: Bearer <token>

{
  "topic_id": "uuid"
}
```

**Response:** 204 No Content

**Errors:**
- `404 Not Found`: Card or topic doesn't exist, or no access to card's deck
- `401 Unauthorized`: Invalid or missing authentication

### Remove Topic from Card
```http
DELETE /api/v1/topics/cards/{card_id}/topics/{topic_id}
Authorization: Bearer <token>
```

**Response:** 204 No Content

---

## Filtering Decks and Cards by Topic

### List Decks Filtered by Topic
```http
GET /api/v1/decks?topic_id={topic_id}&limit=100&offset=0
Authorization: Bearer <token>
```

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Biology 101",
      "description": "...",
      "category": "Science",
      "difficulty": "beginner",
      "card_count": 50,
      "topics": [
        {
          "id": "uuid",
          "name": "Cellular Biology",
          "description": "...",
          "created_at": "...",
          "updated_at": "..."
        }
      ],
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "total": 10,
  "limit": 100,
  "offset": 0
}
```

### List Cards in Deck Filtered by Topic
```http
GET /api/v1/decks/{deck_id}/cards?topic_id={topic_id}&limit=100&offset=0
Authorization: Bearer <token>
```

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "deck_id": "uuid",
      "question": "What is a cell?",
      "answer": "The basic unit of life",
      "source": "Biology101.pdf - Page 5, Section 2.1",
      "source_url": null,
      "topics": [
        {
          "id": "uuid",
          "name": "Cellular Biology",
          "description": "...",
          "created_at": "...",
          "updated_at": "..."
        }
      ],
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "total": 25,
  "limit": 100,
  "offset": 0
}
```

---

## Common Workflows

### 1. Create a Topic and Associate with Deck
```bash
# Step 1: Create topic
curl -X POST http://localhost:8000/api/v1/topics \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Photosynthesis",
    "description": "Process by which plants make food"
  }'
# Response includes topic_id

# Step 2: Associate with deck
curl -X POST http://localhost:8000/api/v1/topics/decks/{deck_id}/topics \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_id": "{topic_id}"
  }'
```

### 2. Add Multiple Topics to a Card
```bash
# Repeat for each topic
curl -X POST http://localhost:8000/api/v1/topics/cards/{card_id}/topics \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_id": "{topic_id_1}"
  }'

curl -X POST http://localhost:8000/api/v1/topics/cards/{card_id}/topics \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_id": "{topic_id_2}"
  }'
```

### 3. Find All Decks About a Specific Topic
```bash
# Get topic ID first
curl http://localhost:8000/api/v1/topics | jq '.items[] | select(.name=="Cellular Biology")'

# Then filter decks
curl http://localhost:8000/api/v1/decks?topic_id={topic_id} \
  -H "Authorization: Bearer <token>"
```

---

## Data Model Relationships

```
Topic (Many) <---> (Many) Deck
  ├── deck_topics (junction table)
  │   ├── deck_id (FK)
  │   ├── topic_id (FK)
  │   └── created_at

Topic (Many) <---> (Many) Card
  ├── card_topics (junction table)
  │   ├── card_id (FK)
  │   ├── topic_id (FK)
  │   └── created_at
```

---

## Business Rules

1. **Topic Names Are Unique**: You cannot create two topics with the same name
2. **Cascade Deletes**: Deleting a topic removes all its associations with decks/cards
3. **Idempotent Associations**: Associating the same topic multiple times has no effect
4. **Authorization**: Only deck/card owners can manage topic associations
5. **Empty Topics Allowed**: Topics don't need to have any associations

---

## Response Codes Summary

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful GET/PUT request |
| 201 | Created | Successfully created topic |
| 204 | No Content | Successfully deleted or associated |
| 400 | Bad Request | Invalid request body |
| 401 | Unauthorized | Missing or invalid auth token |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Topic name already exists |
| 422 | Unprocessable Entity | Validation error |

---

## Notes

- All timestamp fields are in ISO 8601 format (UTC)
- Topic descriptions are optional
- Maximum topic name length: 100 characters
- Maximum topic description length: 500 characters
- Pagination defaults: limit=100, offset=0
