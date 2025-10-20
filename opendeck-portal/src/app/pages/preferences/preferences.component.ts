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
import { ConfirmationService } from 'primeng/api';

// Services
import { LanguageService, SupportedLanguage, LanguageOption } from '../../services/language.service';
import { LayoutService } from '../../layout/service/layout.service';
import { TranslateService } from '@ngx-translate/core';

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
        AppConfigurator
    ],
    providers: [ConfirmationService],
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

    // Available options
    languages: LanguageOption[] = [];

    // Constants
    private readonly SUCCESS_MESSAGE_DURATION = 3000;

    constructor(
        private languageService: LanguageService,
        private layoutService: LayoutService,
        private translate: TranslateService,
        private confirmationService: ConfirmationService
    ) {}

    ngOnInit(): void {
        this.loadPreferences();
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
}
