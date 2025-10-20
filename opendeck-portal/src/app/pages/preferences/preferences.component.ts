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
        AppConfigurator
    ],
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

    constructor(
        private languageService: LanguageService,
        private layoutService: LayoutService,
        private translate: TranslateService
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
        this.languageService.getCurrentLanguage().subscribe(lang => {
            this.selectedLanguage.set(lang);
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

        this.savePreferences();
        this.showSaveSuccess();
    }


    /**
     * Save all preferences to localStorage
     */
    savePreferences(): void {
        // Dark mode is saved automatically by LayoutService
        // Language is already saved by LanguageService
        // Theme colors are managed by the configurator component and saved by LayoutService
    }

    /**
     * Reset preferences to defaults
     */
    resetPreferences(): void {
        this.translate.get('preferences.resetConfirm').subscribe((message: string) => {
            if (confirm(message)) {
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
    }

    /**
     * Show save success message briefly
     */
    showSaveSuccess(): void {
        this.saveSuccess.set(true);
        setTimeout(() => {
            this.saveSuccess.set(false);
        }, 3000);
    }
}
