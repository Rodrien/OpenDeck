import { Injectable } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { BehaviorSubject, Observable } from 'rxjs';

export type SupportedLanguage = 'en' | 'es';

export interface LanguageOption {
    code: SupportedLanguage;
    label: string;
    flag: string;
}

@Injectable({
    providedIn: 'root'
})
export class LanguageService {
    private currentLanguage$ = new BehaviorSubject<SupportedLanguage>('en');

    // Available languages
    readonly availableLanguages: LanguageOption[] = [
        { code: 'en', label: 'English', flag: '🇺🇸' },
        { code: 'es', label: 'Español', flag: '🇪🇸' }
    ];

    constructor(private translate: TranslateService) {
        this.initializeLanguage();
    }

    /**
     * Initialize language from localStorage or browser default
     */
    private initializeLanguage(): void {
        // Try to get saved language from localStorage
        const savedLang = localStorage.getItem('opendeck-language') as SupportedLanguage;

        // Get browser language
        const browserLang = navigator.language.split('-')[0] as SupportedLanguage;

        // Determine which language to use
        let defaultLang: SupportedLanguage = 'en';

        if (savedLang && this.isSupported(savedLang)) {
            defaultLang = savedLang;
        } else if (browserLang && this.isSupported(browserLang)) {
            defaultLang = browserLang;
        }

        this.setLanguage(defaultLang);
    }

    /**
     * Check if a language code is supported
     */
    private isSupported(lang: string): lang is SupportedLanguage {
        return ['en', 'es'].includes(lang);
    }

    /**
     * Set the current language
     */
    setLanguage(lang: SupportedLanguage): void {
        this.translate.use(lang);
        this.currentLanguage$.next(lang);
        localStorage.setItem('opendeck-language', lang);

        // Update HTML lang attribute for accessibility
        document.documentElement.lang = lang;
    }

    /**
     * Get current language as observable
     */
    getCurrentLanguage(): Observable<SupportedLanguage> {
        return this.currentLanguage$.asObservable();
    }

    /**
     * Get current language value (synchronous)
     */
    getCurrentLanguageValue(): SupportedLanguage {
        return this.currentLanguage$.value;
    }

    /**
     * Get language label by code
     */
    getLanguageLabel(lang: SupportedLanguage): string {
        const language = this.availableLanguages.find(l => l.code === lang);
        return language?.label || 'English';
    }

    /**
     * Get language flag emoji by code
     */
    getLanguageFlag(lang: SupportedLanguage): string {
        const language = this.availableLanguages.find(l => l.code === lang);
        return language?.flag || '🇺🇸';
    }

    /**
     * Toggle between English and Spanish
     */
    toggleLanguage(): void {
        const currentLang = this.getCurrentLanguageValue();
        const newLang: SupportedLanguage = currentLang === 'en' ? 'es' : 'en';
        this.setLanguage(newLang);
    }
}
