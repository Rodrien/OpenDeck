import { Component, OnInit, OnDestroy, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

// PrimeNG Imports
import { Card } from 'primeng/card';
import { Button } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { Textarea } from 'primeng/textarea';
import { Select } from 'primeng/select';
import { FileUpload, FileUploadModule, FileUploadHandlerEvent } from 'primeng/fileupload';
import { ProgressBar } from 'primeng/progressbar';
import { Message } from 'primeng/message';
import { Chip } from 'primeng/chip';
import { Divider } from 'primeng/divider';
import { ProgressSpinner } from 'primeng/progressspinner';

// Services
import { DocumentService } from '../../../services/document.service';

// Models
import {
  DeckMetadata,
  CATEGORY_OPTIONS,
  DIFFICULTY_OPTIONS,
  UPLOAD_CONSTRAINTS,
  DocumentStatus,
  CategoryOption,
  DifficultyOption
} from '../../../models/document.model';

interface UploadedFile {
  file: File;
  size: string;
  error?: string;
}

@Component({
  selector: 'app-deck-upload',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    TranslateModule,
    Card,
    Button,
    InputText,
    Textarea,
    Select,
    FileUploadModule,
    ProgressBar,
    Message,
    Chip,
    Divider,
    ProgressSpinner
  ],
  templateUrl: './deck-upload.html',
  styleUrl: './deck-upload.scss'
})
export class DeckUpload implements OnInit, OnDestroy {
  // Reactive form
  uploadForm!: FormGroup;

  // Signals for reactive state
  selectedFiles = signal<UploadedFile[]>([]);
  uploadProgress = signal<number>(0);
  isUploading = signal<boolean>(false);
  uploadError = signal<string | null>(null);
  uploadSuccess = signal<boolean>(false);
  processingStatuses = signal<DocumentStatus[]>([]);
  isPolling = signal<boolean>(false);
  generatedDeckId = signal<string | null>(null);

  // Options for dropdowns
  categoryOptions = CATEGORY_OPTIONS;
  difficultyOptions = DIFFICULTY_OPTIONS;

  // Constants
  readonly MAX_FILES = UPLOAD_CONSTRAINTS.MAX_FILES;
  readonly MAX_FILE_SIZE = UPLOAD_CONSTRAINTS.MAX_FILE_SIZE;
  readonly MAX_TOTAL_SIZE = UPLOAD_CONSTRAINTS.MAX_TOTAL_SIZE;
  readonly ACCEPTED_FILE_TYPES = '.pdf,.docx,.pptx,.txt';

  // Computed values
  totalSize = computed(() => {
    const files = this.selectedFiles();
    const bytes = files.reduce((sum, f) => sum + f.file.size, 0);
    return this.formatFileSize(bytes);
  });

  isFormValid = computed(() => {
    return this.uploadForm?.valid && this.selectedFiles().length > 0 && !this.isUploading();
  });

  allProcessingComplete = computed(() => {
    const statuses = this.processingStatuses();
    if (statuses.length === 0) return false;
    return statuses.every(s => s.status === 'completed' || s.status === 'failed');
  });

  // Cleanup
  private destroy$ = new Subject<void>();

  constructor(
    private fb: FormBuilder,
    private documentService: DocumentService,
    private router: Router,
    private translate: TranslateService
  ) {}

  ngOnInit(): void {
    this.initializeForm();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Initialize the reactive form with validators
   */
  private initializeForm(): void {
    this.uploadForm = this.fb.group({
      title: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(100)]],
      description: ['', [Validators.maxLength(500)]],
      category: [null, [Validators.required]],
      difficulty: [null, [Validators.required]]
    });
  }

  /**
   * Handle file selection from FileUpload component
   */
  onFileSelect(event: any): void {
    const files: File[] = event.currentFiles || [];
    this.uploadError.set(null);

    // Validate file count
    if (files.length > this.MAX_FILES) {
      this.uploadError.set(`Maximum ${this.MAX_FILES} files allowed`);
      return;
    }

    // Validate each file and create UploadedFile objects
    const uploadedFiles: UploadedFile[] = [];
    let hasError = false;

    for (const file of files) {
      const error = this.documentService.validateFile(file);

      uploadedFiles.push({
        file,
        size: this.formatFileSize(file.size),
        error: error || undefined
      });

      if (error) {
        hasError = true;
      }
    }

    // Validate total size
    const totalSizeError = this.documentService.validateTotalSize(files);
    if (totalSizeError) {
      this.uploadError.set(totalSizeError);
      return;
    }

    if (hasError) {
      this.uploadError.set('Some files have validation errors. Please check and try again.');
    }

    this.selectedFiles.set(uploadedFiles);
  }

  /**
   * Remove a file from selection
   */
  removeFile(index: number, fileUpload: any): void {
    const files = this.selectedFiles();
    files.splice(index, 1);
    this.selectedFiles.set([...files]);

    // Update FileUpload component
    fileUpload.files = files.map(f => f.file);
    this.uploadError.set(null);
  }

  /**
   * Handle form submission and file upload
   */
  onSubmit(): void {
    if (!this.isFormValid()) {
      return;
    }

    this.isUploading.set(true);
    this.uploadError.set(null);
    this.uploadSuccess.set(false);
    this.uploadProgress.set(0);

    const metadata: DeckMetadata = {
      title: this.uploadForm.value.title,
      description: this.uploadForm.value.description || undefined,
      category: this.uploadForm.value.category,
      difficulty: this.uploadForm.value.difficulty
    };

    const files = this.selectedFiles().map(f => f.file);

    // Subscribe to upload progress
    this.documentService.getUploadProgress()
      .pipe(takeUntil(this.destroy$))
      .subscribe(progress => {
        this.uploadProgress.set(progress);
      });

    // Upload documents
    this.documentService.uploadDocuments(files, metadata)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          if (response) {
            this.uploadSuccess.set(true);
            this.generatedDeckId.set(response.deck_id);
            this.isUploading.set(false);

            // Start polling for processing status
            this.startPollingStatus(response.document_ids);
          }
        },
        error: (error) => {
          this.uploadError.set(error.message || 'Upload failed. Please try again.');
          this.isUploading.set(false);
          this.uploadProgress.set(0);
        }
      });
  }

  /**
   * Start polling document processing status
   */
  private startPollingStatus(documentIds: string[]): void {
    this.isPolling.set(true);

    this.documentService.pollProcessingStatus(documentIds)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (statuses) => {
          this.processingStatuses.set(statuses);

          // Check if all processing is complete
          if (this.allProcessingComplete()) {
            this.isPolling.set(false);
          }
        },
        error: (error) => {
          console.error('Error polling status:', error);
          this.isPolling.set(false);
        }
      });
  }

  /**
   * Navigate to the flashcard viewer for the generated deck
   */
  viewDeck(): void {
    const deckId = this.generatedDeckId();
    if (deckId) {
      this.router.navigate(['/pages/flashcards/viewer', deckId]);
    }
  }

  /**
   * Reset form and start over
   */
  uploadAnother(): void {
    this.uploadForm.reset();
    this.selectedFiles.set([]);
    this.uploadProgress.set(0);
    this.uploadSuccess.set(false);
    this.uploadError.set(null);
    this.processingStatuses.set([]);
    this.generatedDeckId.set(null);
    this.isPolling.set(false);
  }

  /**
   * Navigate back to decks list
   */
  backToDecks(): void {
    this.router.navigate(['/pages/flashcards']);
  }

  /**
   * Get severity class for processing status
   */
  getStatusSeverity(status: string): 'success' | 'secondary' | 'info' | 'warn' | 'danger' | 'contrast' {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'info';
      case 'pending':
        return 'secondary';
      case 'failed':
        return 'danger';
      default:
        return 'secondary';
    }
  }

  /**
   * Get icon for processing status
   */
  getStatusIcon(status: string): string {
    switch (status) {
      case 'completed':
        return 'pi-check-circle';
      case 'processing':
        return 'pi-spin pi-spinner';
      case 'pending':
        return 'pi-clock';
      case 'failed':
        return 'pi-times-circle';
      default:
        return 'pi-circle';
    }
  }

  /**
   * Format file size for display
   */
  private formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  }
}
