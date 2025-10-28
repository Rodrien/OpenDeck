/**
 * Document Upload Models
 * Types and interfaces for document upload and processing
 */

/**
 * Deck Metadata for Upload
 * Information provided by user when uploading documents
 */
export interface DeckMetadata {
  title: string;
  description?: string;
  category: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
}

/**
 * Upload Response
 * Response from backend after successful document upload
 */
export interface UploadResponse {
  success: boolean;
  deck_id: string;
  document_ids: string[];
  message: string;
}

/**
 * Document Processing Status
 * Current state of document processing
 */
export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';

/**
 * Individual Document Status
 * Status information for a single uploaded document
 */
export interface DocumentStatus {
  document_id: string;
  filename: string;
  status: ProcessingStatus;
  progress: number; // 0-100
  error_message?: string;
  page_count?: number;
  cards_generated?: number;
}

/**
 * File Upload Error
 * Error information for failed uploads
 */
export interface FileUploadError {
  filename: string;
  error: string;
}

/**
 * Supported File Types
 */
export const SUPPORTED_FILE_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
  'application/vnd.openxmlformats-officedocument.presentationml.presentation', // .pptx
  'text/plain'
];

export const SUPPORTED_FILE_EXTENSIONS = ['.pdf', '.docx', '.pptx', '.txt'];

/**
 * Upload Constraints
 */
export const UPLOAD_CONSTRAINTS = {
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB per file
  MAX_TOTAL_SIZE: 50 * 1024 * 1024, // 50MB total
  MAX_FILES: 10
};

/**
 * Category Options
 * Available subject categories for deck classification
 */
export interface CategoryOption {
  label: string;
  value: string;
  icon: string;
}

export const CATEGORY_OPTIONS: CategoryOption[] = [
  { label: 'Mathematics', value: 'Mathematics', icon: 'pi-calculator' },
  { label: 'Computer Science', value: 'Computer Science', icon: 'pi-code' },
  { label: 'Physics', value: 'Physics', icon: 'pi-bolt' },
  { label: 'Chemistry', value: 'Chemistry', icon: 'pi-flask' },
  { label: 'Biology', value: 'Biology', icon: 'pi-leaf' },
  { label: 'History', value: 'History', icon: 'pi-globe' },
  { label: 'Literature', value: 'Literature', icon: 'pi-book' },
  { label: 'Economics', value: 'Economics', icon: 'pi-chart-line' },
  { label: 'Art', value: 'Art', icon: 'pi-palette' },
  { label: 'Music', value: 'Music', icon: 'pi-volume-up' },
  { label: 'Language', value: 'Language', icon: 'pi-comments' },
  { label: 'Other', value: 'Other', icon: 'pi-tags' }
];

/**
 * Difficulty Options
 */
export interface DifficultyOption {
  label: string;
  value: 'beginner' | 'intermediate' | 'advanced';
  icon: string;
}

export const DIFFICULTY_OPTIONS: DifficultyOption[] = [
  { label: 'Beginner', value: 'beginner', icon: 'pi-star' },
  { label: 'Intermediate', value: 'intermediate', icon: 'pi-star-fill' },
  { label: 'Advanced', value: 'advanced', icon: 'pi-bolt' }
];
