/**
 * Deck Comments Component
 * Displays and manages comments for a deck
 */

import { Component, Input, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { InputTextareaModule } from 'primeng/inputtextarea';
import { AvatarModule } from 'primeng/avatar';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ToastModule } from 'primeng/toast';
import { PaginatorModule } from 'primeng/paginator';
import { TranslateModule } from '@ngx-translate/core';
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
    InputTextareaModule,
    AvatarModule,
    ConfirmDialogModule,
    ToastModule,
    PaginatorModule,
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
  currentUser = computed(() => this.authService.currentUser());
  isAuthenticated = computed(() => this.authService.isAuthenticated());
  hasComments = computed(() => this.comments().length > 0);

  constructor(
    private commentService: CommentService,
    private authService: AuthService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService
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
          summary: 'Error',
          detail: 'Failed to load comments'
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
        summary: 'Authentication Required',
        detail: 'Please log in to comment'
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
        summary: 'Comment Too Long',
        detail: 'Comments cannot exceed 5000 characters'
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
          summary: 'Success',
          detail: 'Comment posted successfully'
        });
        // Reload comments to show new one
        this.loadComments();
      },
      error: (error) => {
        console.error('Failed to create comment:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to post comment'
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
        summary: 'Comment Too Long',
        detail: 'Comments cannot exceed 5000 characters'
      });
      return;
    }

    this.commentService.updateComment(this.deckId, commentId, { content }).subscribe({
      next: (updatedComment) => {
        this.editingCommentId.set(null);
        this.editingContent.set('');
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Comment updated successfully'
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
          summary: 'Error',
          detail: 'Failed to update comment'
        });
      }
    });
  }

  /**
   * Delete a comment
   */
  deleteComment(comment: DeckComment): void {
    this.confirmationService.confirm({
      message: 'Are you sure you want to delete this comment?',
      header: 'Delete Comment',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        this.commentService.deleteComment(this.deckId, comment.id).subscribe({
          next: () => {
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Comment deleted successfully'
            });
            this.loadComments();
          },
          error: (error) => {
            console.error('Failed to delete comment:', error);
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to delete comment'
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
        summary: 'Authentication Required',
        detail: 'Please log in to vote'
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
            summary: 'Error',
            detail: 'Failed to record vote'
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
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    if (diffSec < 60) return 'just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHour < 24) return `${diffHour}h ago`;
    if (diffDay < 30) return `${diffDay}d ago`;
    return date.toLocaleDateString();
  }
}
