# OpenDeck Document Upload Testing Guide

This guide will walk you through testing the new document upload and AI flashcard generation feature.

## Prerequisites

Before testing, ensure you have:
- ✅ Docker and Docker Compose installed
- ✅ Anthropic API key (or OpenAI API key)
- ✅ Git repository cloned locally

## Setup Instructions

### 1. Set Your API Key

Create a `.env` file in the project root (or set environment variable):

```bash
# For Anthropic Claude (recommended)
export ANTHROPIC_API_KEY="your-anthropic-api-key-here"

# Or add to .env file
echo "ANTHROPIC_API_KEY=your-anthropic-api-key-here" > .env
```

**How to get an Anthropic API key:**
1. Visit https://console.anthropic.com/
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-ant-...`)

**Alternative - Use OpenAI:**
If you prefer OpenAI, edit `docker-compose.yml` to comment out Anthropic and uncomment OpenAI:
```yaml
# - AI_PROVIDER=anthropic
# - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
- AI_PROVIDER=openai
- OPENAI_API_KEY=${OPENAI_API_KEY}
- OPENAI_MODEL=gpt-4
```

### 2. Start the Application

```bash
# Start all services (backend, frontend, database, redis, celery worker)
docker-compose up --build
```

Wait for all services to start. You should see:
- ✅ `opendeck-db` - PostgreSQL database running
- ✅ `opendeck-redis` - Redis running
- ✅ `opendeck-backend` - FastAPI backend on port 8000
- ✅ `opendeck-celery-worker` - Celery worker ready
- ✅ `opendeck-frontend` - Angular frontend on port 80

### 3. Verify Services are Running

Open a new terminal and run:

```bash
# Check all containers are running
docker-compose ps

# Test backend health
curl http://localhost:8000/health

# Check API documentation
open http://localhost:8000/docs
```

## Test Documents

The repository includes two test documents in `documents/test/`:

1. **Biology101_CellStructure.txt** (9,100+ words)
   - Topic: Cell biology fundamentals
   - Difficulty: Beginner to Intermediate
   - Coverage: Cell structure, organelles, functions
   - Expected cards: 15-25 flashcards

2. **ComputerScience_DataStructures.txt** (2,800+ words)
   - Topic: Data structures and algorithms
   - Difficulty: Beginner
   - Coverage: Arrays, linked lists, stacks, queues, trees, graphs
   - Expected cards: 12-20 flashcards

## Testing Steps

### Step 1: Access the Application

1. Open your browser and navigate to: **http://localhost:4200**
2. You should see the OpenDeck homepage
3. Log in with test credentials (if authentication is enabled):
   - Email: `test@opendeck.com`
   - Password: `password123`

### Step 2: Navigate to Upload Page

1. From the main menu, click **"Upload Documents"** (cloud upload icon)
2. Or navigate directly to: **http://localhost:4200/pages/flashcards/upload**
3. You should see the upload form with:
   - File upload area (drag-and-drop or browse)
   - Title field
   - Description field
   - Category dropdown
   - Difficulty selector

### Step 3: Upload Test Documents

#### Test Case 1: Single Document Upload

1. **Fill out the form:**
   - Title: "Biology 101 - Cell Structure"
   - Description: "Comprehensive study guide for cell biology fundamentals"
   - Category: "Science"
   - Difficulty: "Intermediate"

2. **Upload file:**
   - Click "Choose" or drag and drop: `documents/test/Biology101_CellStructure.txt`
   - Verify file appears in the preview list
   - Check that file size is shown (should be ~60KB)

3. **Submit:**
   - Click "Upload and Generate Flashcards" button
   - Button should show loading state
   - Progress bar should appear

4. **Monitor Progress:**
   - You should see real-time status updates
   - Status will change: Pending → Processing → Completed
   - Watch for "Cards Generated" count to appear
   - Expected: 15-25 flashcards generated

#### Test Case 2: Multiple Documents Upload

1. **Fill out the form:**
   - Title: "Computer Science Fundamentals"
   - Description: "Data structures and algorithms study deck"
   - Category: "Computer Science"
   - Difficulty: "Beginner"

2. **Upload both files:**
   - Add: `documents/test/Biology101_CellStructure.txt`
   - Add: `documents/test/ComputerScience_DataStructures.txt`
   - Verify both files are listed

3. **Submit and monitor:**
   - Each document will be processed separately
   - You'll see individual progress for each file
   - Total flashcards will be combined in one deck

#### Test Case 3: File Validation

Test the validation by trying to upload:

1. **Too many files:**
   - Try uploading 11 files (max is 10)
   - Should show error: "Maximum 10 files allowed"

2. **Invalid file type:**
   - Try uploading a .jpg or .zip file
   - Should show error: "Only PDF, DOCX, PPTX, TXT files are allowed"

3. **File too large:**
   - Try uploading a file > 10MB
   - Should show error: "File exceeds maximum size of 10MB"

4. **Form validation:**
   - Try submitting without a title
   - Try submitting without selecting category
   - Form should prevent submission

### Step 4: View Generated Flashcards

1. After processing completes, click **"View Deck"**
2. You should see the flashcard viewer with all generated cards
3. **Verify flashcard quality:**
   - Questions are clear and focused
   - Answers are comprehensive but concise
   - **Source attribution is present** (e.g., "Biology101_CellStructure.txt - Page 1, Section 1.1")

4. **Test flashcard functionality:**
   - Click card to flip (show answer)
   - Navigate between cards
   - Mark cards as known/unknown
   - Check that counters update

### Step 5: Check Backend Logs

Monitor the processing in real-time by checking logs:

```bash
# Backend API logs
docker-compose logs -f backend

# Celery worker logs (shows AI processing)
docker-compose logs -f celery_worker

# Redis logs
docker-compose logs -f redis
```

**What to look for:**
- ✅ File upload success messages
- ✅ Celery task queued
- ✅ Document processing started
- ✅ AI API calls (to Anthropic or OpenAI)
- ✅ Flashcards parsed and validated
- ✅ Database records created
- ✅ Task completed successfully

### Step 6: Verify Database Records

Check that data was persisted correctly:

```bash
# Connect to PostgreSQL container
docker-compose exec db psql -U opendeck_user -d opendeck

# Check decks
SELECT id, title, category, difficulty, card_count, created_at FROM decks ORDER BY created_at DESC LIMIT 5;

# Check documents
SELECT id, filename, status, deck_id, processed_at FROM documents ORDER BY created_at DESC LIMIT 5;

# Check flashcards with source attribution
SELECT id, question, answer, source FROM cards WHERE deck_id = 'YOUR_DECK_ID' LIMIT 5;

# Exit
\q
```

## Expected Results

### Success Criteria

After completing the test cases, you should observe:

1. **Upload Process:**
   - ✅ Files upload successfully
   - ✅ Form validation works correctly
   - ✅ Progress tracking is real-time and accurate

2. **Processing:**
   - ✅ Celery worker picks up tasks
   - ✅ AI API is called successfully
   - ✅ Processing completes within 1-3 minutes per document
   - ✅ No errors in logs

3. **Flashcard Generation:**
   - ✅ 15-25 cards generated from Biology document
   - ✅ 12-20 cards generated from CS document
   - ✅ All cards have source attribution
   - ✅ Questions are relevant to document content
   - ✅ Answers are accurate and helpful

4. **Data Persistence:**
   - ✅ Deck created in database
   - ✅ Documents linked to deck
   - ✅ Flashcards saved with source field
   - ✅ Card count matches actual cards

5. **User Experience:**
   - ✅ UI is responsive and intuitive
   - ✅ Error messages are clear
   - ✅ Loading states are visible
   - ✅ Navigation works smoothly

## Troubleshooting

### Issue: "AI Provider Error"

**Cause:** API key not set or invalid

**Solution:**
```bash
# Check if API key is set
echo $ANTHROPIC_API_KEY

# Set it if missing
export ANTHROPIC_API_KEY="your-key-here"

# Restart services
docker-compose restart backend celery_worker
```

### Issue: Files upload but processing never starts

**Cause:** Celery worker not running or Redis connection issue

**Solution:**
```bash
# Check Celery worker status
docker-compose logs celery_worker

# Check Redis connectivity
docker-compose exec backend redis-cli -h redis ping
# Should return: PONG

# Restart services
docker-compose restart celery_worker redis
```

### Issue: "Source attribution missing" errors

**Cause:** AI model not following prompt instructions

**Solution:**
- This is handled automatically - the code adds default source if missing
- Check logs to see how many cards needed source correction
- Consider using a more powerful model (e.g., Claude Opus or GPT-4)

### Issue: Processing takes too long (> 5 minutes)

**Cause:** Large documents or slow AI API responses

**Solutions:**
1. Check document size (keep under 15,000 characters for best results)
2. Increase Celery timeout in `docker-compose.yml`:
   ```yaml
   - CELERY_TASK_TIME_LIMIT=1800  # 30 minutes
   ```
3. Use a faster AI model
4. Split large documents into smaller files

### Issue: Docker containers won't start

**Solution:**
```bash
# Clean up and rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

## Performance Benchmarks

Expected processing times (with Claude 3.5 Sonnet):

| Document Size | Processing Time | Cards Generated |
|---------------|----------------|-----------------|
| 1-2 pages     | 10-20 seconds  | 5-10 cards      |
| 3-5 pages     | 20-40 seconds  | 10-15 cards     |
| 6-10 pages    | 40-90 seconds  | 15-25 cards     |
| 10+ pages     | 90+ seconds    | 25+ cards       |

*Processing time includes: file upload, text extraction, AI generation, database writes*

## Testing Checklist

Use this checklist to ensure comprehensive testing:

- [ ] Set up API key correctly
- [ ] All Docker containers are running
- [ ] Upload page loads without errors
- [ ] Single file upload works
- [ ] Multiple file upload works
- [ ] File validation (too many files)
- [ ] File validation (wrong file type)
- [ ] File validation (file too large)
- [ ] Form validation (missing required fields)
- [ ] Progress tracking displays correctly
- [ ] Status polling updates in real-time
- [ ] Processing completes successfully
- [ ] Flashcards are generated
- [ ] Source attribution is present on all cards
- [ ] Flashcard viewer works
- [ ] Database records are created
- [ ] No errors in backend logs
- [ ] No errors in Celery logs
- [ ] Can navigate back to decks list
- [ ] Can upload another deck

## Advanced Testing

### Load Testing

Test with multiple concurrent uploads:

```bash
# Install Apache Bench
brew install httpd  # macOS
# or: apt-get install apache2-utils  # Linux

# Test concurrent uploads (requires authentication token)
ab -n 10 -c 2 -H "Authorization: Bearer YOUR_TOKEN" -p upload.json -T "application/json" http://localhost:8000/api/v1/documents/upload
```

### Integration Testing

Run backend tests:

```bash
# Run all tests
docker-compose exec backend pytest

# Run specific test file
docker-compose exec backend pytest tests/test_document_processing.py

# Run with coverage
docker-compose exec backend pytest --cov=app tests/
```

## API Testing with curl

Test the API directly:

```bash
# Login to get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@opendeck.com","password":"password123"}' \
  | jq -r '.access_token')

# Upload document
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@documents/test/Biology101_CellStructure.txt" \
  -F "title=Biology Test" \
  -F "description=Test upload" \
  -F "category=Science" \
  -F "difficulty=intermediate"

# Check status (use document_id from response)
curl -X GET "http://localhost:8000/api/v1/documents/status?document_ids=DOCUMENT_ID" \
  -H "Authorization: Bearer $TOKEN"
```

## Monitoring and Observability

### View Celery Tasks

```bash
# Access Celery flower (if configured)
open http://localhost:5555

# Or check Redis directly
docker-compose exec redis redis-cli
> KEYS celery*
> LLEN celery
```

### Check Storage

```bash
# View uploaded files
docker-compose exec backend ls -lh /app/storage/documents/

# Check disk usage
docker-compose exec backend du -sh /app/storage/documents/
```

## Next Steps

After successful testing:

1. **Create more test documents** with different subjects and formats
2. **Test with PDF and DOCX files** (not just TXT)
3. **Customize AI prompts** in `backend/app/services/ai_service.py`
4. **Adjust flashcard count** (max_cards parameter)
5. **Enable user authentication** and test with multiple users
6. **Set up monitoring** (CloudWatch, DataDog, etc.)
7. **Deploy to staging** environment
8. **Conduct user acceptance testing** (UAT)

## Support

If you encounter issues not covered in this guide:

1. Check the logs: `docker-compose logs -f`
2. Review the implementation plan: `.claude/plans/document-upload-deck-generation.md`
3. Check the API documentation: http://localhost:8000/docs
4. Review the frontend documentation: `opendeck-portal/DECK_UPLOAD_IMPLEMENTATION.md`

---

**Happy Testing! 🚀📚**

Generated on: 2025-10-25 for OpenDeck v1.0.0
