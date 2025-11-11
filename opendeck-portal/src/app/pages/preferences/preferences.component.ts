import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import { trigger, transition, style, animate } from '@angular/animations';

// PrimeNG Imports
import { Card } from 'primeng/card';
import { Button } from 'primeng/button';
import { Select } from 'primeng/select';
import { Divider } from 'primeng/divider';
import { Message } from 'primeng/message';
import { ConfirmDialog } from 'primeng/confirmdialog';
import { ConfirmationService, MessageService } from 'primeng/api';
import { FileUpload } from 'primeng/fileupload';
import { AvatarModule } from 'primeng/avatar';
import { ToastModule } from 'primeng/toast';

// Services
import { LanguageService, SupportedLanguage, LanguageOption } from '../../services/language.service';
import { LayoutService } from '../../layout/service/layout.service';
import { TranslateService } from '@ngx-translate/core';
import { AuthService } from '../../services/auth.service';
import { UserService } from '../../services/user.service';
import { User } from '../../models/user.model';

// Components
import { AppConfigurator } from '../../layout/component/app.configurator';

@Component({
    selector: 'app-preferences',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        TranslateModule,
        Card,
        Button,
        Select,
        Divider,
        Message,
        ConfirmDialog,
        FileUpload,
        AvatarModule,
        ToastModule,
        AppConfigurator
    ],
    providers: [ConfirmationService, MessageService],
    templateUrl: './preferences.component.html',
    styleUrls: ['./preferences.component.scss'],
    animations: [
        trigger('fadeIn', [
            transition(':enter', [
                style({ opacity: 0, transform: 'translateY(-10px)' }),
                animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
            ])
        ])
    ]
})
export class PreferencesComponent implements OnInit {
    // Signals for reactive state
    selectedLanguage = signal<SupportedLanguage>('en');
    isDarkMode = signal<boolean>(false);
    saveSuccess = signal<boolean>(false);
    currentUser = signal<User | null>(null);
    uploadingPicture = signal<boolean>(false);
    imagePreview = signal<string | null>(null);

    // Available options
    languages: LanguageOption[] = [];

    // Constants
    private readonly SUCCESS_MESSAGE_DURATION = 3000;
    private readonly MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
    private readonly ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

    constructor(
        private languageService: LanguageService,
        private layoutService: LayoutService,
        private translate: TranslateService,
        private confirmationService: ConfirmationService,
        private authService: AuthService,
        private userService: UserService,
        private messageService: MessageService
    ) {}

    ngOnInit(): void {
        this.loadPreferences();
        this.loadCurrentUser();
    }

    /**
     * Load current preferences from services and localStorage
     */
    private loadPreferences(): void {
        // Load language options
        this.languages = this.languageService.availableLanguages;

        // Get current language
        this.languageService.getCurrentLanguage().subscribe({
            next: (lang) => {
                this.selectedLanguage.set(lang);
            },
            error: (err) => {
                console.error('Error loading language:', err);
                this.selectedLanguage.set('en'); // fallback to English
            }
        });

        // Get current theme state
        this.isDarkMode.set(this.layoutService.isDarkTheme() ?? false);
    }

    /**
     * Load current user data
     */
    private loadCurrentUser(): void {
        const user = this.authService.getCurrentUser();
        this.currentUser.set(user);
    }

    /**
     * Handle language change
     */
    onLanguageChange(newLang: SupportedLanguage): void {
        this.languageService.setLanguage(newLang);
        this.selectedLanguage.set(newLang);
        this.showSaveSuccess();
    }

    /**
     * Toggle dark mode
     */
    toggleDarkMode(): void {
        const newDarkMode = !this.isDarkMode();
        this.isDarkMode.set(newDarkMode);

        // Update layout service
        this.layoutService.layoutConfig.update((state) => ({
            ...state,
            darkTheme: newDarkMode
        }));

        this.showSaveSuccess();
    }
    /**
     * Reset preferences to defaults
     */
    resetPreferences(): void {
        this.translate.get(['preferences.resetConfirm', 'preferences.confirmHeader', 'common.yes', 'common.no'])
            .subscribe({
                next: (translations) => {
                    this.confirmationService.confirm({
                        message: translations['preferences.resetConfirm'],
                        header: translations['preferences.confirmHeader'] || 'Confirm',
                        icon: 'pi pi-exclamation-triangle',
                        acceptLabel: translations['common.yes'] || 'Yes',
                        rejectLabel: translations['common.no'] || 'No',
                        accept: () => {
                            // Reset to defaults
                            this.selectedLanguage.set('en');
                            this.isDarkMode.set(false);

                            // Apply changes
                            this.languageService.setLanguage('en');
                            this.layoutService.layoutConfig.update((state) => ({
                                ...state,
                                darkTheme: false,
                                preset: 'Aura',
                                primary: 'emerald',
                                surface: null,
                                menuMode: 'static'
                            }));

                            // Note: localStorage is automatically updated by LayoutService
                            this.showSaveSuccess();
                        }
                    });
                },
                error: (err) => {
                    console.error('Error loading translations:', err);
                    // Fallback to English
                    this.confirmationService.confirm({
                        message: 'Are you sure you want to reset all preferences to their default values?',
                        header: 'Confirm',
                        icon: 'pi pi-exclamation-triangle',
                        acceptLabel: 'Yes',
                        rejectLabel: 'No',
                        accept: () => {
                            this.selectedLanguage.set('en');
                            this.isDarkMode.set(false);
                            this.languageService.setLanguage('en');
                            this.layoutService.layoutConfig.update((state) => ({
                                ...state,
                                darkTheme: false,
                                preset: 'Aura',
                                primary: 'emerald',
                                surface: null,
                                menuMode: 'static'
                            }));
                            this.showSaveSuccess();
                        }
                    });
                }
            });
    }

    /**
     * Show save success message briefly
     */
    showSaveSuccess(): void {
        this.saveSuccess.set(true);
        setTimeout(() => {
            this.saveSuccess.set(false);
        }, this.SUCCESS_MESSAGE_DURATION);
    }

    /**
     * Handle file selection for profile picture
     */
    onFileSelect(event: any): void {
        const file = event.files[0];

        // Validate file
        if (!this.validateFile(file)) {
            return;
        }

        // Show preview
        const reader = new FileReader();
        reader.onload = (e: any) => {
            this.imagePreview.set(e.target.result);
        };
        reader.readAsDataURL(file);

        // Upload file
        this.uploadProfilePicture(file);
    }

    /**
     * Validate file type and size
     */
    private validateFile(file: File): boolean {
        // Check file type
        if (!this.ALLOWED_TYPES.includes(file.type)) {
            this.messageService.add({
                severity: 'error',
                summary: this.translate.instant('common.error'),
                detail: this.translate.instant('preferences.profilePicture.invalidType')
            });
            return false;
        }

        // Check file size
        if (file.size > this.MAX_FILE_SIZE) {
            this.messageService.add({
                severity: 'error',
                summary: this.translate.instant('common.error'),
                detail: this.translate.instant('preferences.profilePicture.fileTooLarge')
            });
            return false;
        }

        return true;
    }

    /**
     * Upload profile picture
     */
    private uploadProfilePicture(file: File): void {
        this.uploadingPicture.set(true);

        this.userService.uploadProfilePicture(file).subscribe({
            next: (updatedUser) => {
                this.currentUser.set(updatedUser);
                this.imagePreview.set(null);
                this.uploadingPicture.set(false);

                // Update auth service user
                this.authService.currentUser$.subscribe();

                this.messageService.add({
                    severity: 'success',
                    summary: this.translate.instant('common.success'),
                    detail: this.translate.instant('preferences.profilePicture.uploadSuccess')
                });
            },
            error: (error) => {
                console.error('Failed to upload profile picture:', error);
                this.imagePreview.set(null);
                this.uploadingPicture.set(false);

                this.messageService.add({
                    severity: 'error',
                    summary: this.translate.instant('common.error'),
                    detail: this.translate.instant('preferences.profilePicture.uploadFailed')
                });
            }
        });
    }

    /**
     * Remove profile picture
     */
    removeProfilePicture(): void {
        this.translate.get([
            'preferences.profilePicture.removeConfirm',
            'preferences.profilePicture.removeHeader',
            'common.yes',
            'common.no'
        ]).subscribe({
            next: (translations) => {
                this.confirmationService.confirm({
                    message: translations['preferences.profilePicture.removeConfirm'],
                    header: translations['preferences.profilePicture.removeHeader'],
                    icon: 'pi pi-exclamation-triangle',
                    acceptLabel: translations['common.yes'],
                    rejectLabel: translations['common.no'],
                    accept: () => {
                        this.userService.deleteProfilePicture().subscribe({
                            next: (updatedUser) => {
                                this.currentUser.set(updatedUser);

                                this.messageService.add({
                                    severity: 'success',
                                    summary: this.translate.instant('common.success'),
                                    detail: this.translate.instant('preferences.profilePicture.removeSuccess')
                                });
                            },
                            error: (error) => {
                                console.error('Failed to remove profile picture:', error);

                                this.messageService.add({
                                    severity: 'error',
                                    summary: this.translate.instant('common.error'),
                                    detail: this.translate.instant('preferences.profilePicture.removeFailed')
                                });
                            }
                        });
                    }
                });
            }
        });
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
}
