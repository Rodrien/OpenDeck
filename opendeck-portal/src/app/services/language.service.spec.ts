import { TestBed } from '@angular/core/testing';
import { LanguageService, SupportedLanguage } from './language.service';
import { TranslateService } from '@ngx-translate/core';

describe('LanguageService', () => {
    let service: LanguageService;
    let translateService: jasmine.SpyObj<TranslateService>;
    let localStorageSpy: jasmine.Spy;
    let documentLangSpy: jasmine.Spy;

    beforeEach(() => {
        const translateServiceSpy = jasmine.createSpyObj('TranslateService', ['use']);

        // Mock localStorage
        let store: { [key: string]: string } = {};
        spyOn(localStorage, 'getItem').and.callFake((key: string) => store[key] || null);
        spyOn(localStorage, 'setItem').and.callFake((key: string, value: string) => {
            store[key] = value;
        });
        spyOn(localStorage, 'clear').and.callFake(() => {
            store = {};
        });

        TestBed.configureTestingModule({
            providers: [
                LanguageService,
                { provide: TranslateService, useValue: translateServiceSpy }
            ]
        });

        translateService = TestBed.inject(TranslateService) as jasmine.SpyObj<TranslateService>;

        // Reset localStorage before each test
        localStorage.clear();
    });

    describe('initialization', () => {
        it('should create', () => {
            service = TestBed.inject(LanguageService);
            expect(service).toBeTruthy();
        });

        it('should initialize with English when no saved language exists', () => {
            // Mock navigator.language to return a non-supported language
            Object.defineProperty(navigator, 'language', {
                writable: true,
                configurable: true,
                value: 'fr-FR'
            });

            service = TestBed.inject(LanguageService);

            expect(translateService.use).toHaveBeenCalledWith('en');
            expect(localStorage.setItem).toHaveBeenCalledWith('opendeck-language', 'en');
        });

        it('should initialize with saved language from localStorage', () => {
            localStorage.setItem('opendeck-language', 'es');

            service = TestBed.inject(LanguageService);

            expect(translateService.use).toHaveBeenCalledWith('es');
        });

        it('should initialize with browser language if supported', () => {
            Object.defineProperty(navigator, 'language', {
                writable: true,
                configurable: true,
                value: 'es-MX'
            });

            service = TestBed.inject(LanguageService);

            expect(translateService.use).toHaveBeenCalledWith('es');
        });

        it('should prefer saved language over browser language', () => {
            localStorage.setItem('opendeck-language', 'en');
            Object.defineProperty(navigator, 'language', {
                writable: true,
                configurable: true,
                value: 'es-ES'
            });

            service = TestBed.inject(LanguageService);

            expect(translateService.use).toHaveBeenCalledWith('en');
        });
    });

    describe('availableLanguages', () => {
        it('should have English and Spanish available', () => {
            service = TestBed.inject(LanguageService);

            expect(service.availableLanguages).toEqual([
                { code: 'en', label: 'English', flag: '🇺🇸' },
                { code: 'es', label: 'Español', flag: '🇪🇸' }
            ]);
        });

        it('should be readonly', () => {
            service = TestBed.inject(LanguageService);
            const languages = service.availableLanguages;

            expect(() => {
                // @ts-ignore - intentionally trying to reassign readonly property
                service.availableLanguages = [];
            }).toThrow();
        });
    });

    describe('setLanguage', () => {
        beforeEach(() => {
            service = TestBed.inject(LanguageService);
        });

        it('should set language to English', () => {
            service.setLanguage('en');

            expect(translateService.use).toHaveBeenCalledWith('en');
            expect(localStorage.setItem).toHaveBeenCalledWith('opendeck-language', 'en');
        });

        it('should set language to Spanish', () => {
            service.setLanguage('es');

            expect(translateService.use).toHaveBeenCalledWith('es');
            expect(localStorage.setItem).toHaveBeenCalledWith('opendeck-language', 'es');
        });

        it('should update HTML lang attribute for accessibility', () => {
            const originalLang = document.documentElement.lang;

            service.setLanguage('es');
            expect(document.documentElement.lang).toBe('es');

            service.setLanguage('en');
            expect(document.documentElement.lang).toBe('en');

            // Cleanup
            document.documentElement.lang = originalLang;
        });

        it('should emit new language value to subscribers', (done) => {
            service.getCurrentLanguage().subscribe(lang => {
                if (lang === 'es') {
                    expect(lang).toBe('es');
                    done();
                }
            });

            service.setLanguage('es');
        });
    });

    describe('getCurrentLanguage', () => {
        beforeEach(() => {
            service = TestBed.inject(LanguageService);
        });

        it('should return current language as observable', (done) => {
            service.setLanguage('en');

            service.getCurrentLanguage().subscribe(lang => {
                expect(lang).toBe('en');
                done();
            });
        });

        it('should emit new values when language changes', () => {
            const emittedValues: SupportedLanguage[] = [];

            service.getCurrentLanguage().subscribe(lang => {
                emittedValues.push(lang);
            });

            service.setLanguage('es');

            expect(emittedValues).toContain('es');
        });
    });

    describe('getCurrentLanguageValue', () => {
        beforeEach(() => {
            service = TestBed.inject(LanguageService);
        });

        it('should return current language synchronously', () => {
            service.setLanguage('en');
            expect(service.getCurrentLanguageValue()).toBe('en');

            service.setLanguage('es');
            expect(service.getCurrentLanguageValue()).toBe('es');
        });
    });

    describe('getLanguageLabel', () => {
        beforeEach(() => {
            service = TestBed.inject(LanguageService);
        });

        it('should return "English" for en code', () => {
            expect(service.getLanguageLabel('en')).toBe('English');
        });

        it('should return "Español" for es code', () => {
            expect(service.getLanguageLabel('es')).toBe('Español');
        });

        it('should return "English" as fallback for invalid code', () => {
            // @ts-ignore - intentionally passing invalid code
            expect(service.getLanguageLabel('invalid')).toBe('English');
        });
    });

    describe('getLanguageFlag', () => {
        beforeEach(() => {
            service = TestBed.inject(LanguageService);
        });

        it('should return US flag for en code', () => {
            expect(service.getLanguageFlag('en')).toBe('🇺🇸');
        });

        it('should return Spanish flag for es code', () => {
            expect(service.getLanguageFlag('es')).toBe('🇪🇸');
        });

        it('should return US flag as fallback for invalid code', () => {
            // @ts-ignore - intentionally passing invalid code
            expect(service.getLanguageFlag('invalid')).toBe('🇺🇸');
        });
    });

    describe('toggleLanguage', () => {
        beforeEach(() => {
            service = TestBed.inject(LanguageService);
        });

        it('should toggle from English to Spanish', () => {
            service.setLanguage('en');
            service.toggleLanguage();

            expect(service.getCurrentLanguageValue()).toBe('es');
            expect(translateService.use).toHaveBeenCalledWith('es');
        });

        it('should toggle from Spanish to English', () => {
            service.setLanguage('es');
            service.toggleLanguage();

            expect(service.getCurrentLanguageValue()).toBe('en');
            expect(translateService.use).toHaveBeenCalledWith('en');
        });

        it('should persist toggled language to localStorage', () => {
            service.setLanguage('en');
            service.toggleLanguage();

            expect(localStorage.setItem).toHaveBeenCalledWith('opendeck-language', 'es');
        });
    });

    describe('isSupported (private method behavior)', () => {
        beforeEach(() => {
            service = TestBed.inject(LanguageService);
        });

        it('should accept supported languages through setLanguage', () => {
            expect(() => service.setLanguage('en')).not.toThrow();
            expect(() => service.setLanguage('es')).not.toThrow();
        });

        it('should handle unsupported languages gracefully in initialization', () => {
            localStorage.setItem('opendeck-language', 'fr' as any);
            Object.defineProperty(navigator, 'language', {
                writable: true,
                configurable: true,
                value: 'de-DE'
            });

            // Service should fall back to 'en' for unsupported languages
            const newService = TestBed.inject(LanguageService);
            expect(newService.getCurrentLanguageValue()).toBe('en');
        });
    });
});
