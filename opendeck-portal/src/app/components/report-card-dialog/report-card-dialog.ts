import { Component, EventEmitter, Input, Output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TranslateModule, TranslateService } from '@ngx-translate/core';

// PrimeNG Components
import { DialogModule } from 'primeng/dialog';
import { ButtonModule } from 'primeng/button';
import { TextareaModule } from 'primeng/textarea';
import { MessageModule } from 'primeng/message';
import { MessageService } from 'primeng/api';

// Services
import { CardService } from '../../services/card.service';

/**
 * Report Card Dialog Component
 * Allows users to report flashcards with incorrect, misleading, or unhelpful information
 */
@Component({
  selector: 'app-report-card-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TranslateModule,
    DialogModule,
    ButtonModule,
    TextareaModule,
    MessageModule
  ],
  templateUrl: './report-card-dialog.html',
  styleUrl: './report-card-dialog.scss'
})
export class ReportCardDialog {
  @Input() visible = false;
  @Input() cardId = '';
  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() reportSubmitted = new EventEmitter<void>();

  // Reactive state
  reason = signal('');
  isSubmitting = signal(false);
  readonly MIN_REASON_LENGTH = 10;
  readonly MAX_REASON_LENGTH = 1000;

  constructor(
    private cardService: CardService,
    private messageService: MessageService,
    private translate: TranslateService
  ) {}

  /**
   * Check if the reason meets minimum length requirement
   */
  get isReasonValid(): boolean {
    const trimmedLength = this.reason().trim().length;
    return trimmedLength >= this.MIN_REASON_LENGTH && trimmedLength <= this.MAX_REASON_LENGTH;
  }

  /**
   * Calculate remaining characters needed to meet minimum
   */
  get remainingChars(): number {
    return this.MIN_REASON_LENGTH - this.reason().trim().length;
  }

  /**
   * Get current character count
   */
  get currentLength(): number {
    return this.reason().trim().length;
  }

  /**
   * Handle dialog close
   */
  onHide(): void {
    this.reason.set('');
    this.visibleChange.emit(false);
  }

  /**
   * Submit the report
   */
  onSubmit(): void {
    if (!this.isReasonValid || this.isSubmitting()) {
      return;
    }

    this.isSubmitting.set(true);

    this.cardService.reportCard(this.cardId, { reason: this.reason().trim() })
      .subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: this.translate.instant('common.success'),
            detail: this.translate.instant('reportCard.successMessage')
          });
          this.reportSubmitted.emit();
          this.onHide();
          this.isSubmitting.set(false);
        },
        error: (error) => {
          console.error('Error reporting card:', error);
          this.messageService.add({
            severity: 'error',
            summary: this.translate.instant('common.error'),
            detail: this.translate.instant('reportCard.errorMessage')
          });
          this.isSubmitting.set(false);
        }
      });
  }
}
