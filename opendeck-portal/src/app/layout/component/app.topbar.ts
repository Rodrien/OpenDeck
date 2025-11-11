import { Component, OnInit, signal, ViewChild, DestroyRef, inject } from '@angular/core';
import { MenuItem, ConfirmationService, MessageService } from 'primeng/api';
import { RouterModule, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { AvatarModule } from 'primeng/avatar';
import { Menu } from 'primeng/menu';
import { ConfirmDialog } from 'primeng/confirmdialog';
import { Dialog } from 'primeng/dialog';
import { Button } from 'primeng/button';
import { Select } from 'primeng/select';
import { Textarea } from 'primeng/textarea';
import { Message } from 'primeng/message';
import { Toast } from 'primeng/toast';
import { Tooltip } from 'primeng/tooltip';
import { LayoutService } from '../service/layout.service';
import { AuthService } from '../../services/auth.service';
import { FeedbackService, FeedbackType } from '../../services/feedback.service';
import { User } from '../../models/user.model';
import { TranslateService, TranslateModule, LangChangeEvent } from '@ngx-translate/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { firstValueFrom } from 'rxjs';
import { NotificationBellComponent } from '../../components/notification-bell/notification-bell.component';

interface TranslationMap {
    [key: string]: string;
}

@Component({
    selector: 'app-topbar',
    standalone: true,
    imports: [
        RouterModule,
        CommonModule,
        ReactiveFormsModule,
        TranslateModule,
        AvatarModule,
        Menu,
        ConfirmDialog,
        Dialog,
        Button,
        Select,
        Textarea,
        Message,
        Toast,
        Tooltip,
        NotificationBellComponent
    ],
    providers: [ConfirmationService, MessageService],
    template: `
        <p-confirmDialog />
        <p-toast position="top-right" />

        <div class="layout-topbar">
            <div class="layout-topbar-logo-container">
                <button class="layout-menu-button layout-topbar-action" (click)="layoutService.onMenuToggle()">
                    <i class="pi pi-bars"></i>
                </button>
                <a class="layout-topbar-logo" routerLink="/">
                    <img src="images/opendeck_line_cropped.png" alt="OpenDeck Logo" class="opendeck-logo" />
                </a>
            </div>

            <div class="layout-topbar-actions">
                <!-- Dark Mode Toggle -->
                <button
                    type="button"
                    class="layout-topbar-action"
                    (click)="toggleDarkMode()"
                    [attr.aria-pressed]="isDarkMode()"
                    [attr.aria-label]="darkModeAriaLabel()"
                >
                    <i [class]="isDarkMode() ? 'pi pi-moon' : 'pi pi-sun'"></i>
                </button>

                <!-- Feedback Button -->
                <button
                    type="button"
                    class="layout-topbar-action"
                    (click)="showFeedbackDialog()"
                    [attr.aria-label]="feedbackAriaLabel()"
                    pTooltip="{{ feedbackAriaLabel() }}"
                    tooltipPosition="bottom"
                >
                    <i class="pi pi-comment"></i>
                </button>

                <!-- Notification Bell -->
                <app-notification-bell></app-notification-bell>

                <!-- User Avatar -->
                <div class="user-avatar-container">
                    <button
                        type="button"
                        class="avatar-button p-0 border-none bg-transparent cursor-pointer"
                        (click)="toggleUserMenu($event)"
                        [attr.aria-label]="userMenuAriaLabel()"
                    >
                        @if (currentUser()?.profilePictureUrl) {
                            <p-avatar
                                [image]="currentUser()!.profilePictureUrl"
                                styleClass="bg-primary text-white"
                                shape="circle"
                                size="large"
                            ></p-avatar>
                        } @else {
                            <p-avatar
                                [label]="getUserInitials()"
                                styleClass="bg-primary text-white"
                                shape="circle"
                                size="large"
                            ></p-avatar>
                        }
                    </button>
                    <p-menu #userMenu [model]="userMenuItems" [popup]="true" appendTo="body" styleClass="user-menu">
                        <ng-template pTemplate="start">
                            <div class="user-menu-header">
                                <div class="flex items-center gap-3 p-3 border-bottom-1 surface-border">
                                    <div class="flex flex-col">
                                        <span class="font-semibold text-surface-900 dark:text-surface-0">{{ currentUser()?.name || userDisplayName() }}</span>
                                        <span class="text-muted-color text-sm">{{ currentUser()?.email || userEmailDisplay() }}</span>
                                    </div>
                                </div>
                            </div>
                        </ng-template>
                    </p-menu>
                </div>
            </div>
        </div>

        <!-- Feedback Dialog -->
        <p-dialog
            [(visible)]="feedbackDialogVisible"
            [header]="feedbackDialogTitle()"
            [modal]="true"
            [draggable]="false"
            [resizable]="false"
            [closable]="true"
            [dismissableMask]="true"
            styleClass="feedback-dialog"
            [style]="{width: '500px', maxWidth: '90vw'}"
        >
            <div class="feedback-dialog-content">
                <p class="text-muted-color mb-4">{{ feedbackDescription() }}</p>

                <form [formGroup]="feedbackForm" (ngSubmit)="submitFeedback()">
                    <!-- Feedback Type -->
                    <div class="mb-4">
                        <label for="feedbackType" class="block mb-2 font-semibold">
                            {{ feedbackTypeLabel() }}
                        </label>
                        <p-select
                            id="feedbackType"
                            formControlName="type"
                            [options]="feedbackTypeOptions"
                            optionLabel="label"
                            optionValue="value"
                            [placeholder]="feedbackTypePlaceholder()"
                            styleClass="w-full"
                        />
                    </div>

                    <!-- Message -->
                    <div class="mb-4">
                        <label for="feedbackMessage" class="block mb-2 font-semibold">
                            {{ feedbackMessageLabel() }}
                        </label>
                        <textarea
                            pTextarea
                            id="feedbackMessage"
                            formControlName="message"
                            [placeholder]="feedbackMessagePlaceholder()"
                            rows="6"
                            class="w-full"
                            [class.ng-invalid]="feedbackForm.get('message')?.invalid && feedbackForm.get('message')?.touched"
                        ></textarea>

                        @if (feedbackForm.get('message')?.invalid && feedbackForm.get('message')?.touched) {
                            <p-message
                                severity="error"
                                [text]="getMessageError()"
                                styleClass="mt-2 w-full"
                            />
                        }

                        <small class="text-muted-color block mt-1">
                            {{ feedbackForm.get('message')?.value?.length || 0 }} / 10 {{ 'feedback.characters' | translate }}
                        </small>
                    </div>

                    <!-- Action Buttons -->
                    <div class="flex justify-end gap-2">
                        <p-button
                            [label]="feedbackCancelLabel()"
                            severity="secondary"
                            [outlined]="true"
                            (onClick)="closeFeedbackDialog()"
                            [disabled]="isSubmittingFeedback()"
                        />
                        <p-button
                            type="submit"
                            [label]="feedbackSubmitLabel()"
                            icon="pi pi-send"
                            [disabled]="feedbackForm.invalid || isSubmittingFeedback()"
                            [loading]="isSubmittingFeedback()"
                        />
                    </div>
                </form>
            </div>
        </p-dialog>
    `
})
export class AppTopbar implements OnInit {
    @ViewChild('userMenu', { static: false }) userMenu!: Menu;
    items!: MenuItem[];
    currentUser = signal<User | null>(null);
    userMenuItems: MenuItem[] = [];
    isDarkMode = signal<boolean>(false);
    darkModeAriaLabel = signal<string>('');
    userMenuAriaLabel = signal<string>('');
    userDisplayName = signal<string>('User');
    userEmailDisplay = signal<string>('Not logged in');

    // Feedback dialog state
    feedbackDialogVisible = false;
    feedbackForm!: FormGroup;
    feedbackTypeOptions: Array<{label: string, value: FeedbackType}> = [];
    isSubmittingFeedback = signal<boolean>(false);

    // Feedback dialog translations
    feedbackAriaLabel = signal<string>('Send Feedback');
    feedbackDialogTitle = signal<string>('Send Feedback');
    feedbackDescription = signal<string>('');
    feedbackTypeLabel = signal<string>('Feedback Type');
    feedbackTypePlaceholder = signal<string>('Select feedback type');
    feedbackMessageLabel = signal<string>('Your Message');
    feedbackMessagePlaceholder = signal<string>('Tell us what\'s on your mind...');
    feedbackSubmitLabel = signal<string>('Send Feedback');
    feedbackCancelLabel = signal<string>('Cancel');
    feedbackSuccessMessage = signal<string>('Thank you for your feedback!');
    feedbackErrorMessage = signal<string>('Failed to submit feedback.');

    private destroyRef = inject(DestroyRef);
    private fb = inject(FormBuilder);
    private feedbackService = inject(FeedbackService);
    private messageService = inject(MessageService);

    constructor(
        public layoutService: LayoutService,
        private authService: AuthService,
        private router: Router,
        private confirmationService: ConfirmationService,
        private translate: TranslateService
    ) {
        // Subscribe to current user changes with automatic cleanup
        this.authService.currentUser$
            .pipe(takeUntilDestroyed())
            .subscribe(user => {
                this.currentUser.set(user);
            });

        // Initialize feedback form
        this.initializeFeedbackForm();
    }

    /**
     * Toggle dark mode
     */
    toggleDarkMode(): void {
        const newDarkMode = !this.isDarkMode();
        this.isDarkMode.set(newDarkMode);

        // Update layout service (automatically saved to localStorage)
        this.layoutService.layoutConfig.update((state) => ({
            ...state,
            darkTheme: newDarkMode
        }));

        // Update aria label to reflect new state
        this.updateDarkModeLabel();
    }

    ngOnInit(): void {
        // Initialize dark mode from layout service
        this.isDarkMode.set(this.layoutService.isDarkTheme() ?? false);

        // Initialize translations
        this.updateTranslations();
        this.updateFeedbackTranslations();

        // Initialize menu items
        this.updateUserMenuItems();

        // Update menu items and translations when language changes
        this.translate.onLangChange
            .pipe(takeUntilDestroyed(this.destroyRef))
            .subscribe(() => {
                this.updateTranslations();
                this.updateUserMenuItems();
                this.updateFeedbackTranslations();
            });
    }

    /**
     * Update translations for aria-labels and user display
     */
    private async updateTranslations(): Promise<void> {
        const translations = await firstValueFrom(
            this.translate.get([
                'topbar.switchToLightMode',
                'topbar.switchToDarkMode',
                'topbar.userMenu',
                'topbar.user',
                'topbar.notLoggedIn',
                'topbar.feedback'
            ])
        );

        // Update dark mode aria label based on current state
        const label = this.isDarkMode()
            ? (translations['topbar.switchToLightMode'] || 'Switch to light mode')
            : (translations['topbar.switchToDarkMode'] || 'Switch to dark mode');
        this.darkModeAriaLabel.set(label);

        // Update user menu aria label
        this.userMenuAriaLabel.set(translations['topbar.userMenu'] || 'User menu');

        // Update user display defaults
        this.userDisplayName.set(translations['topbar.user'] || 'User');
        this.userEmailDisplay.set(translations['topbar.notLoggedIn'] || 'Not logged in');

        // Update feedback aria label
        this.feedbackAriaLabel.set(translations['topbar.feedback'] || 'Send Feedback');
    }

    /**
     * Update dark mode aria label based on current state
     */
    private async updateDarkModeLabel(): Promise<void> {
        const translations = await firstValueFrom(
            this.translate.get(['topbar.switchToLightMode', 'topbar.switchToDarkMode'])
        );

        const label = this.isDarkMode()
            ? (translations['topbar.switchToLightMode'] || 'Switch to light mode')
            : (translations['topbar.switchToDarkMode'] || 'Switch to dark mode');
        this.darkModeAriaLabel.set(label);
    }

    /**
     * Update user menu items with current translations
     */
    private async updateUserMenuItems(): Promise<void> {
        const translations = await firstValueFrom(
            this.translate.get(['common.preferences', 'auth.logout'])
        );

        this.userMenuItems = [
            {
                label: translations['common.preferences'] || 'Preferences',
                icon: 'pi pi-cog',
                command: () => this.navigateToPreferences()
            },
            {
                separator: true
            },
            {
                label: translations['auth.logout'] || 'Logout',
                icon: 'pi pi-sign-out',
                command: () => this.logout()
            }
        ];
    }

    toggleUserMenu(event: Event) {
        event.stopPropagation();
        if (this.userMenu) {
            this.userMenu.toggle(event);
        } else {
            console.error('userMenu is not defined');
        }
    }

    async logout() {
        let translations;

        try {
            translations = await firstValueFrom(
                this.translate.get(['auth.logoutConfirm', 'auth.logoutHeader', 'common.yes', 'common.no'])
            );
        } catch (err) {
            console.error('Error loading translations:', err);
            // Default English translations
            translations = {
                'auth.logoutConfirm': 'Are you sure you want to logout?',
                'auth.logoutHeader': 'Confirm Logout',
                'common.yes': 'Yes',
                'common.no': 'No'
            };
        }

        // Single confirmation dialog setup
        this.confirmationService.confirm({
            message: translations['auth.logoutConfirm'],
            header: translations['auth.logoutHeader'],
            icon: 'pi pi-sign-out',
            acceptLabel: translations['common.yes'],
            rejectLabel: translations['common.no'],
            accept: async () => {
                await this.authService.logout();
            }
        });
    }

    navigateToPreferences() {
        this.router.navigate(['/pages/preferences']);
    }

    /**
     * Get user initials for avatar
     */
    getUserInitials(): string {
        const user = this.currentUser();
        if (!user || !user.name) return 'U';

        const parts = user.name.split(' ');
        if (parts.length >= 2) {
            return (parts[0][0] + parts[1][0]).toUpperCase();
        }
        return user.name.substring(0, 2).toUpperCase();
    }

    /**
     * Initialize feedback form
     */
    private initializeFeedbackForm(): void {
        this.feedbackForm = this.fb.group({
            type: [FeedbackType.GENERAL, Validators.required],
            message: ['', [Validators.required, Validators.minLength(10)]]
        });
    }

    /**
     * Update feedback dialog translations
     */
    private async updateFeedbackTranslations(): Promise<void> {
        const translations = await firstValueFrom(
            this.translate.get([
                'feedback.title',
                'feedback.description',
                'feedback.typeLabel',
                'feedback.typePlaceholder',
                'feedback.messageLabel',
                'feedback.messagePlaceholder',
                'feedback.submit',
                'feedback.cancel',
                'feedback.successMessage',
                'feedback.errorMessage',
                'feedback.types.bugReport',
                'feedback.types.featureRequest',
                'feedback.types.generalFeedback',
                'feedback.types.other'
            ])
        );

        this.feedbackDialogTitle.set(translations['feedback.title'] || 'Send Feedback');
        this.feedbackDescription.set(translations['feedback.description'] || '');
        this.feedbackTypeLabel.set(translations['feedback.typeLabel'] || 'Feedback Type');
        this.feedbackTypePlaceholder.set(translations['feedback.typePlaceholder'] || 'Select feedback type');
        this.feedbackMessageLabel.set(translations['feedback.messageLabel'] || 'Your Message');
        this.feedbackMessagePlaceholder.set(translations['feedback.messagePlaceholder'] || 'Tell us what\'s on your mind...');
        this.feedbackSubmitLabel.set(translations['feedback.submit'] || 'Send Feedback');
        this.feedbackCancelLabel.set(translations['feedback.cancel'] || 'Cancel');
        this.feedbackSuccessMessage.set(translations['feedback.successMessage'] || 'Thank you for your feedback!');
        this.feedbackErrorMessage.set(translations['feedback.errorMessage'] || 'Failed to submit feedback.');

        // Update feedback type options
        this.feedbackTypeOptions = [
            {
                label: translations['feedback.types.bugReport'] || 'Bug Report',
                value: FeedbackType.BUG
            },
            {
                label: translations['feedback.types.featureRequest'] || 'Feature Request',
                value: FeedbackType.FEATURE
            },
            {
                label: translations['feedback.types.generalFeedback'] || 'General Feedback',
                value: FeedbackType.GENERAL
            },
            {
                label: translations['feedback.types.other'] || 'Other',
                value: FeedbackType.OTHER
            }
        ];
    }

    /**
     * Show feedback dialog
     */
    showFeedbackDialog(): void {
        this.feedbackDialogVisible = true;
        this.feedbackForm.reset({
            type: FeedbackType.GENERAL,
            message: ''
        });
    }

    /**
     * Close feedback dialog
     */
    closeFeedbackDialog(): void {
        this.feedbackDialogVisible = false;
        this.feedbackForm.reset();
        this.isSubmittingFeedback.set(false);
    }

    /**
     * Submit feedback
     */
    async submitFeedback(): Promise<void> {
        if (this.feedbackForm.invalid) {
            this.feedbackForm.markAllAsTouched();
            return;
        }

        this.isSubmittingFeedback.set(true);

        try {
            const feedbackData = {
                feedback_type: this.feedbackForm.value.type,
                message: this.feedbackForm.value.message.trim()
            };

            await firstValueFrom(this.feedbackService.submitFeedback(feedbackData));

            // Show success toast
            this.messageService.add({
                severity: 'success',
                summary: this.feedbackDialogTitle(),
                detail: this.feedbackSuccessMessage(),
                life: 5000
            });

            // Close dialog and reset form
            this.closeFeedbackDialog();
        } catch (error) {
            console.error('Error submitting feedback:', error);

            // Show error toast
            this.messageService.add({
                severity: 'error',
                summary: this.feedbackDialogTitle(),
                detail: this.feedbackErrorMessage(),
                life: 5000
            });

            this.isSubmittingFeedback.set(false);
        }
    }

    /**
     * Get message validation error text
     */
    getMessageError(): string {
        const messageControl = this.feedbackForm.get('message');
        if (!messageControl) return '';

        if (messageControl.hasError('required')) {
            return this.translate.instant('feedback.messageRequired');
        }

        if (messageControl.hasError('minlength')) {
            const requiredLength = messageControl.errors?.['minlength']?.requiredLength || 10;
            const currentLength = messageControl.value?.length || 0;
            const remaining = requiredLength - currentLength;
            return this.translate.instant('feedback.messageMinLength', { count: remaining });
        }

        return '';
    }
}
