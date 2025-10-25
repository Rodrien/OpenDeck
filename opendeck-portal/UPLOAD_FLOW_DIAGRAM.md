# Document Upload Flow Diagram

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      DeckUpload Component                         │
│                                                                   │
│  ┌─────────────────┐    ┌──────────────────┐                   │
│  │  Reactive Form  │    │  Signal State    │                   │
│  │  - title        │    │  - selectedFiles │                   │
│  │  - description  │    │  - uploadProgress│                   │
│  │  - category     │    │  - isUploading   │                   │
│  │  - difficulty   │    │  - uploadSuccess │                   │
│  └─────────────────┘    │  - uploadError   │                   │
│                         │  - processingStatuses│                │
│                         └──────────────────┘                   │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  Template Structure                         │ │
│  │  ┌──────────────┐  ┌───────────────┐                      │ │
│  │  │ File Upload  │  │ Metadata Form │                      │ │
│  │  │  Section     │  │   Section     │                      │ │
│  │  └──────────────┘  └───────────────┘                      │ │
│  │                                                             │ │
│  │  ┌──────────────────────────────────────┐                 │ │
│  │  │     Upload Progress Display          │                 │ │
│  │  └──────────────────────────────────────┘                 │ │
│  │                                                             │ │
│  │  ┌──────────────────────────────────────┐                 │ │
│  │  │   Processing Status Display          │                 │ │
│  │  └──────────────────────────────────────┘                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Computed Properties                            │ │
│  │  - totalSize()           (file sizes)                      │ │
│  │  - isFormValid()         (validation)                      │ │
│  │  - allProcessingComplete()  (status)                       │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ uses
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DocumentService                                │
│                                                                   │
│  Methods:                                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ uploadDocuments(files, metadata)                          │  │
│  │   → POST /api/v1/documents/upload                         │  │
│  │   → Returns: Observable<UploadResponse>                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ getProcessingStatus(documentIds)                          │  │
│  │   → GET /api/v1/documents/status                          │  │
│  │   → Returns: Observable<DocumentStatus[]>                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ pollProcessingStatus(documentIds)                         │  │
│  │   → Polls every 2 seconds                                 │  │
│  │   → Stops when all complete/failed                        │  │
│  │   → Returns: Observable<DocumentStatus[]>                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ validateFile(file)                                        │  │
│  │   → Returns: string | null                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## User Flow

```
┌──────────────┐
│ User arrives │
│  at upload   │
│     page     │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│  1. Select Files                     │
│     - Drag & drop OR click to browse │
│     - Max 10 files                   │
│     - PDF, DOCX, PPTX, TXT           │
│     - Client-side validation         │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  2. Fill Deck Metadata               │
│     - Title (required)               │
│     - Description (optional)         │
│     - Category (required)            │
│     - Difficulty (required)          │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  3. Review & Submit                  │
│     - See file list                  │
│     - Total size display             │
│     - Remove files if needed         │
│     - Click "Generate Flashcards"    │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  4. Upload Progress                  │
│     - Progress bar (0-100%)          │
│     - Loading state                  │
│     - Upload to backend              │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  5. Upload Success                   │
│     - Success message                │
│     - Deck ID received               │
│     - Document IDs received          │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  6. Processing Status (Auto-poll)    │
│     - Poll every 2 seconds           │
│     - Show per-document status:      │
│       • Pending (gray)               │
│       • Processing (blue + progress) │
│       • Completed (green + count)    │
│       • Failed (red + error)         │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  7. Processing Complete              │
│     - All documents processed        │
│     - Action buttons appear:         │
│       • View Deck                    │
│       • Upload Another               │
│       • Back to Decks                │
└──────────────────────────────────────┘
```

## State Flow Diagram

```
                    ┌─────────────────┐
                    │  Initial State  │
                    │ uploadSuccess=F │
                    │ isUploading=F   │
                    │ selectedFiles=[]│
                    └────────┬────────┘
                             │
                     User selects files
                             │
                             ▼
                    ┌─────────────────┐
                    │  Files Selected │
                    │ selectedFiles=N │
                    └────────┬────────┘
                             │
                    User fills form & submits
                             │
                             ▼
                    ┌─────────────────┐
                    │   Uploading     │
                    │ isUploading=T   │
                    │ uploadProgress  │
                    │   updating      │
                    └────────┬────────┘
                             │
                    Upload completes
                             │
                             ▼
                    ┌─────────────────┐
                    │ Upload Success  │
                    │ uploadSuccess=T │
                    │ isUploading=F   │
                    │ deckId received │
                    └────────┬────────┘
                             │
                    Start status polling
                             │
                             ▼
                    ┌─────────────────┐
                    │   Processing    │
                    │ isPolling=T     │
                    │ statuses update │
                    │   every 2s      │
                    └────────┬────────┘
                             │
            All documents complete/failed
                             │
                             ▼
                    ┌─────────────────┐
                    │    Complete     │
                    │ isPolling=F     │
                    │ allProcessing   │
                    │  Complete=T     │
                    └─────────────────┘
```

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Error Scenarios                       │
└─────────────────────────────────────────────────────────┘

1. File Validation Errors
   ├─ Too many files (>10)
   │  └─> Show error message, don't accept files
   ├─ File too large (>10MB)
   │  └─> Mark file with error badge
   ├─ Wrong file type
   │  └─> Mark file with error badge
   └─ Total size too large (>50MB)
      └─> Show error message below file list

2. Upload Errors
   ├─ Network error
   │  └─> Show error message: "Unable to connect to server"
   ├─ Server error (500)
   │  └─> Show error message: "Server error. Try again later"
   ├─ Bad request (400)
   │  └─> Show error message with server details
   └─ File too large (413)
      └─> Show error message: "Files too large. Reduce size"

3. Processing Errors
   ├─ Document processing failed
   │  └─> Show red badge with error message per document
   └─> User can still view deck with successful cards

4. Form Validation Errors
   ├─ Missing required field
   │  └─> Show error below field
   └─ Invalid field value
      └─> Show error below field
      └─> Disable submit button

```

## Data Models

```typescript
// Upload Request
{
  files: File[],              // Array of File objects
  metadata: {
    title: string,            // Required, 3-100 chars
    description?: string,     // Optional, max 500 chars
    category: string,         // Required, from predefined list
    difficulty: string        // Required: 'beginner' | 'intermediate' | 'advanced'
  }
}

// Upload Response
{
  success: boolean,           // Upload success flag
  deck_id: string,            // UUID of created deck
  document_ids: string[],     // Array of document UUIDs
  message: string             // Success message
}

// Document Status
{
  document_id: string,        // UUID
  filename: string,           // Original filename
  status: string,             // 'pending' | 'processing' | 'completed' | 'failed'
  progress: number,           // 0-100
  error_message?: string,     // Error details if failed
  page_count?: number,        // Number of pages processed
  cards_generated?: number    // Number of flashcards created
}
```

## Component Lifecycle

```
┌──────────────────────────────────────────────────────────────┐
│                    Component Lifecycle                         │
└──────────────────────────────────────────────────────────────┘

1. ngOnInit()
   └─> initializeForm()
       └─> Create FormGroup with validators

2. User Interaction
   ├─> onFileSelect(event)
   │   ├─> Validate files
   │   └─> Update selectedFiles signal
   │
   ├─> removeFile(index)
   │   └─> Remove from selectedFiles signal
   │
   └─> onSubmit()
       ├─> Validate form
       ├─> Call documentService.uploadDocuments()
       ├─> Subscribe to upload progress
       ├─> Handle upload response
       └─> Start status polling

3. Status Polling
   └─> startPollingStatus(documentIds)
       ├─> Call documentService.pollProcessingStatus()
       ├─> Update processingStatuses signal
       └─> Stop when all complete/failed

4. ngOnDestroy()
   └─> destroy$.next()
       └─> Cleanup subscriptions
```

## Routing Integration

```
┌────────────────────────────────────────────────────────┐
│                  Application Routes                     │
└────────────────────────────────────────────────────────┘

/pages/flashcards                    → FlashcardDecksListComponent
/pages/flashcards/upload             → DeckUpload (NEW)
/pages/flashcards/viewer/:deckId     → FlashcardViewerComponent

Navigation Flow:
1. User clicks "Upload Documents" in menu
   └─> Navigate to /pages/flashcards/upload

2. After upload completes, user clicks "View Deck"
   └─> Navigate to /pages/flashcards/viewer/:deckId

3. User clicks "Back to Decks"
   └─> Navigate to /pages/flashcards
```

## PrimeNG Component Usage

```
┌────────────────────────────────────────────────────────┐
│              PrimeNG Components Used                    │
└────────────────────────────────────────────────────────┘

File Upload Section:
├─ <p-card> - Container for file upload
├─ <p-fileUpload> - Main file upload component
│  ├─ Custom content template
│  ├─ Drag & drop support
│  └─ Multiple file support
├─ <p-chip> - Error badges for invalid files
├─ <p-button> - Remove file buttons
├─ <p-divider> - Section separator
└─ <p-message> - Error messages

Metadata Form Section:
├─ <p-card> - Container for form
├─ <input pInputText> - Title input
├─ <textarea pTextarea> - Description input
├─ <p-select> - Category dropdown
│  └─ Custom item template with icons
└─ <p-select> - Difficulty dropdown
   └─ Custom item template with icons

Progress Section:
├─ <p-card> - Container
├─ <p-progressBar> - Upload progress
└─ <p-progressSpinner> - Processing spinner

Status Section:
├─ <p-card> - Container
├─ <p-chip> - Status badges
├─ <p-progressBar> - Per-document progress
└─ <p-button> - Action buttons

```
