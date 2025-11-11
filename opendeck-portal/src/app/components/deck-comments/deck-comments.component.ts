/**
 * Deck Comments Component
 * Displays and manages comments for a deck
 */

import { Component, Input, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { Textarea } from 'primeng/textarea';
import { AvatarModule } from 'primeng/avatar';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ToastModule } from 'primeng/toast';
import { PaginatorModule } from 'primeng/paginator';
import { TooltipModule } from 'primeng/tooltip';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { ConfirmationService, MessageService } from 'primeng/api';

import { CommentService } from '../../services/comment.service';
import { AuthService } from '../../services/auth.service';
import { DeckComment, CreateCommentDto, VoteType } from '../../models/comment.model';

@Component({
  selector: 'app-deck-comments',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    CardModule,
    Textarea,
    AvatarModule,
    ConfirmDialogModule,
    ToastModule,
    PaginatorModule,
    TooltipModule,
    TranslateModule
  ],
  providers: [ConfirmationService, MessageService],
  templateUrl: './deck-comments.component.html',
  styleUrls: ['./deck-comments.component.scss']
})
export class DeckCommentsComponent implements OnInit {
  @Input() deckId!: string;

  // Signals
  comments = signal<DeckComment[]>([]);
  loading = signal(false);
  submitting = signal(false);
  totalComments = signal(0);
  currentPage = signal(0);
  pageSize = signal(20);

  // Comment form
  newCommentContent = signal('');
  editingCommentId = signal<string | null>(null);
  editingContent = signal('');

  // Computed values
  currentUser = computed(() => this.authService.getCurrentUser());
  isAuthenticated = computed(() => this.authService.isAuthenticated());
  hasComments = computed(() => this.comments().length > 0);

  constructor(
    private commentService: CommentService,
    private authService: AuthService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService,
    private translate: TranslateService
  ) {}

  ngOnInit(): void {
    this.loadComments();
  }

  /**
   * Load comments for the current page
   */
  loadComments(): void {
    if (!this.deckId) {
      console.error('No deck ID provided');
      return;
    }

    this.loading.set(true);
    const offset = this.currentPage() * this.pageSize();

    this.commentService.getCommentsByDeck(this.deckId, {
      limit: this.pageSize(),
      offset: offset
    }).subscribe({
      next: (response) => {
        this.comments.set(response.items);
        this.totalComments.set(response.total);
        this.loading.set(false);
      },
      error: (error) => {
        console.error('Failed to load comments:', error);
        this.messageService.add({
          severity: 'error',
          summary: this.translate.instant('common.error'),
          detail: this.translate.instant('comments.error.loadFailed')
        });
        this.loading.set(false);
      }
    });
  }

  /**
   * Handle page change from paginator
   */
  onPageChange(event: any): void {
    this.currentPage.set(event.page);
    this.loadComments();
  }

  /**
   * Submit new comment
   */
  submitComment(): void {
    if (!this.isAuthenticated()) {
      this.messageService.add({
        severity: 'warn',
        summary: this.translate.instant('comments.authRequired'),
        detail: this.translate.instant('comments.error.loginRequired')
      });
      return;
    }

    const content = this.newCommentContent().trim();
    if (!content) {
      return;
    }

    if (content.length > 5000) {
      this.messageService.add({
        severity: 'error',
        summary: this.translate.instant('comments.error.tooLong'),
        detail: this.translate.instant('comments.error.tooLongDetail')
      });
      return;
    }

    this.submitting.set(true);
    const dto: CreateCommentDto = { content };

    this.commentService.createComment(this.deckId, dto).subscribe({
      next: (comment) => {
        this.newCommentContent.set('');
        this.submitting.set(false);
        this.messageService.add({
          severity: 'success',
          summary: this.translate.instant('common.success'),
          detail: this.translate.instant('comments.success.posted')
        });
        // Reload comments to show new one
        this.loadComments();
      },
      error: (error) => {
        console.error('Failed to create comment:', error);
        this.messageService.add({
          severity: 'error',
          summary: this.translate.instant('common.error'),
          detail: this.translate.instant('comments.error.postFailed')
        });
        this.submitting.set(false);
      }
    });
  }

  /**
   * Start editing a comment
   */
  startEdit(comment: DeckComment): void {
    this.editingCommentId.set(comment.id);
    this.editingContent.set(comment.content);
  }

  /**
   * Cancel editing
   */
  cancelEdit(): void {
    this.editingCommentId.set(null);
    this.editingContent.set('');
  }

  /**
   * Save edited comment
   */
  saveEdit(commentId: string): void {
    const content = this.editingContent().trim();
    if (!content) {
      return;
    }

    if (content.length > 5000) {
      this.messageService.add({
        severity: 'error',
        summary: this.translate.instant('comments.error.tooLong'),
        detail: this.translate.instant('comments.error.tooLongDetail')
      });
      return;
    }

    this.commentService.updateComment(this.deckId, commentId, { content }).subscribe({
      next: (updatedComment) => {
        this.editingCommentId.set(null);
        this.editingContent.set('');
        this.messageService.add({
          severity: 'success',
          summary: this.translate.instant('common.success'),
          detail: this.translate.instant('comments.success.updated')
        });
        // Update comment in list
        this.comments.update(comments =>
          comments.map(c => c.id === commentId ? updatedComment : c)
        );
      },
      error: (error) => {
        console.error('Failed to update comment:', error);
        this.messageService.add({
          severity: 'error',
          summary: this.translate.instant('common.error'),
          detail: this.translate.instant('comments.error.updateFailed')
        });
      }
    });
  }

  /**
   * Delete a comment
   */
  deleteComment(comment: DeckComment): void {
    this.confirmationService.confirm({
      message: this.translate.instant('comments.confirm.deleteMessage'),
      header: this.translate.instant('comments.confirm.deleteHeader'),
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        this.commentService.deleteComment(this.deckId, comment.id).subscribe({
          next: () => {
            this.messageService.add({
              severity: 'success',
              summary: this.translate.instant('common.success'),
              detail: this.translate.instant('comments.success.deleted')
            });
            this.loadComments();
          },
          error: (error) => {
            console.error('Failed to delete comment:', error);
            this.messageService.add({
              severity: 'error',
              summary: this.translate.instant('common.error'),
              detail: this.translate.instant('comments.error.deleteFailed')
            });
          }
        });
      }
    });
  }

  /**
   * Vote on a comment
   */
  vote(comment: DeckComment, voteType: VoteType): void {
    if (!this.isAuthenticated()) {
      this.messageService.add({
        severity: 'warn',
        summary: this.translate.instant('comments.authRequired'),
        detail: this.translate.instant('comments.error.loginRequiredToVote')
      });
      return;
    }

    // If clicking the same vote type, remove the vote
    if (comment.user_vote === voteType) {
      this.commentService.removeVote(this.deckId, comment.id).subscribe({
        next: () => {
          // Update comment locally
          this.comments.update(comments =>
            comments.map(c => {
              if (c.id === comment.id) {
                const upvotesDelta = voteType === 'upvote' ? -1 : 0;
                const downvotesDelta = voteType === 'downvote' ? -1 : 0;
                return {
                  ...c,
                  upvotes: c.upvotes + upvotesDelta,
                  downvotes: c.downvotes + downvotesDelta,
                  score: c.score - (voteType === 'upvote' ? 1 : -1),
                  user_vote: null
                };
              }
              return c;
            })
          );
        },
        error: (error) => {
          console.error('Failed to remove vote:', error);
        }
      });
    } else {
      // Vote or change vote
      this.commentService.voteOnComment(this.deckId, comment.id, { vote_type: voteType }).subscribe({
        next: (voteCounts) => {
          // Update comment locally
          this.comments.update(comments =>
            comments.map(c =>
              c.id === comment.id
                ? {
                    ...c,
                    upvotes: voteCounts.upvotes,
                    downvotes: voteCounts.downvotes,
                    score: voteCounts.score,
                    user_vote: voteCounts.user_vote
                  }
                : c
            )
          );
        },
        error: (error) => {
          console.error('Failed to vote:', error);
          this.messageService.add({
            severity: 'error',
            summary: this.translate.instant('common.error'),
            detail: this.translate.instant('comments.error.voteFailed')
          });
        }
      });
    }
  }

  /**
   * Check if current user can edit a comment
   */
  canEdit(comment: DeckComment): boolean {
    const user = this.currentUser();
    return !!user && user.id === comment.user_id;
  }

  /**
   * Get user initials for avatar
   */
  getUserInitials(name: string): string {
    if (!name) return '?';
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  }

  /**
   * Format relative time
   */
  getRelativeTime(dateString: string): string {
    // Backend returns naive datetime strings (without timezone info)
    // We need to treat them as UTC and append 'Z' if missing
    let dateStr = dateString;
    if (!dateStr.endsWith('Z') && !dateStr.includes('+') && !dateStr.includes('T00:00:00')) {
      // If the string doesn't have timezone info, assume UTC
      dateStr = dateStr + 'Z';
    }

    // Parse the date string
    const date = new Date(dateStr);

    // Check if date is valid
    if (isNaN(date.getTime())) {
      console.error('Invalid date string:', dateString, 'parsed as:', dateStr);
      return dateString;
    }

    const now = new Date();
    const diffMs = now.getTime() - date.getTime();

    // Handle negative differences (future dates)
    if (diffMs < 0) {
      console.warn('Comment date is in the future:', dateString, 'diff:', diffMs);
      return this.translate.instant('comments.time.justNow');
    }

    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    if (diffSec < 60) return this.translate.instant('comments.time.justNow');
    if (diffMin < 60) return this.translate.instant('comments.time.minutesAgo', { count: diffMin });
    if (diffHour < 24) return this.translate.instant('comments.time.hoursAgo', { count: diffHour });
    if (diffDay < 30) return this.translate.instant('comments.time.daysAgo', { count: diffDay });
    return date.toLocaleDateString();
  }

  /**
   * Update comment content signal
   */
  updateNewCommentContent(value: string): void {
    this.newCommentContent.set(value);
  }

  /**
   * Update editing content signal
   */
  updateEditingContent(value: string): void {
    this.editingContent.set(value);
  }
}
