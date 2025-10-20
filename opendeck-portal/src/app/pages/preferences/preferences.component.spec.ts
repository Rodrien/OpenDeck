import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { PreferencesComponent } from './preferences.component';
import { LanguageService } from '../../services/language.service';
import { LayoutService } from '../../layout/service/layout.service';
import { TranslateService, TranslateModule } from '@ngx-translate/core';
import { ConfirmationService } from 'primeng/api';
import { of, throwError } from 'rxjs';
import { signal } from '@angular/core';

describe('PreferencesComponent', () => {
    let component: PreferencesComponent;
    let fixture: ComponentFixture<PreferencesComponent>;
    let languageService: jasmine.SpyObj<LanguageService>;
    let layoutService: jasmine.SpyObj<LayoutService>;
    let translateService: jasmine.SpyObj<TranslateService>;
    let confirmationService: jasmine.SpyObj<ConfirmationService>;

    beforeEach(async () => {
        const languageServiceSpy = jasmine.createSpyObj('LanguageService', [
            'getCurrentLanguage',
            'setLanguage'
        ], {
            availableLanguages: [
                { code: 'en', label: 'English', flag: '🇺🇸' },
                { code: 'es', label: 'Español', flag: '🇪🇸' }
            ]
        });

        const layoutServiceSpy = jasmine.createSpyObj('LayoutService', ['isDarkTheme'], {
            layoutConfig: signal({
                darkTheme: false,
                preset: 'Aura',
                primary: 'emerald',
                surface: null,
                menuMode: 'static'
            })
        });

        const translateServiceSpy = jasmine.createSpyObj('TranslateService', ['get']);
        const confirmationServiceSpy = jasmine.createSpyObj('ConfirmationService', ['confirm']);

        await TestBed.configureTestingModule({
            imports: [PreferencesComponent, TranslateModule.forRoot()],
            providers: [
                { provide: LanguageService, useValue: languageServiceSpy },
                { provide: LayoutService, useValue: layoutServiceSpy },
                { provide: TranslateService, useValue: translateServiceSpy },
                { provide: ConfirmationService, useValue: confirmationServiceSpy }
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(PreferencesComponent);
        component = fixture.componentInstance;
        languageService = TestBed.inject(LanguageService) as jasmine.SpyObj<LanguageService>;
        layoutService = TestBed.inject(LayoutService) as jasmine.SpyObj<LayoutService>;
        translateService = TestBed.inject(TranslateService) as jasmine.SpyObj<TranslateService>;
        confirmationService = TestBed.inject(ConfirmationService) as jasmine.SpyObj<ConfirmationService>;
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });

    describe('ngOnInit', () => {
        it('should load preferences on initialization', () => {
            languageService.getCurrentLanguage.and.returnValue(of('en'));
            layoutService.isDarkTheme.and.returnValue(false);

            component.ngOnInit();

            expect(component.languages).toEqual(languageService.availableLanguages);
            expect(component.selectedLanguage()).toBe('en');
            expect(component.isDarkMode()).toBe(false);
        });

        it('should handle error when loading language and fallback to English', () => {
            languageService.getCurrentLanguage.and.returnValue(throwError(() => new Error('Language load error')));
            layoutService.isDarkTheme.and.returnValue(false);
            spyOn(console, 'error');

            component.ngOnInit();

            expect(console.error).toHaveBeenCalledWith('Error loading language:', jasmine.any(Error));
            expect(component.selectedLanguage()).toBe('en');
        });

        it('should handle null theme state', () => {
            languageService.getCurrentLanguage.and.returnValue(of('en'));
            layoutService.isDarkTheme.and.returnValue(null);

            component.ngOnInit();

            expect(component.isDarkMode()).toBe(false);
        });
    });

    describe('onLanguageChange', () => {
        it('should set new language and show success message', fakeAsync(() => {
            component.onLanguageChange('es');

            expect(languageService.setLanguage).toHaveBeenCalledWith('es');
            expect(component.selectedLanguage()).toBe('es');
            expect(component.saveSuccess()).toBe(true);

            tick(component['SUCCESS_MESSAGE_DURATION']);

            expect(component.saveSuccess()).toBe(false);
        }));
    });

    describe('toggleDarkMode', () => {
        it('should toggle dark mode from false to true', fakeAsync(() => {
            component.isDarkMode.set(false);

            component.toggleDarkMode();

            expect(component.isDarkMode()).toBe(true);
            expect(component.saveSuccess()).toBe(true);

            tick(component['SUCCESS_MESSAGE_DURATION']);
            expect(component.saveSuccess()).toBe(false);
        }));

        it('should toggle dark mode from true to false', fakeAsync(() => {
            component.isDarkMode.set(true);

            component.toggleDarkMode();

            expect(component.isDarkMode()).toBe(false);
        }));
    });

    describe('resetPreferences', () => {
        it('should show confirmation dialog and reset preferences when accepted', () => {
            const translations = {
                'preferences.resetConfirm': 'Are you sure?',
                'preferences.confirmHeader': 'Confirm',
                'common.yes': 'Yes',
                'common.no': 'No'
            };
            translateService.get.and.returnValue(of(translations));

            let acceptCallback: Function | undefined;
            confirmationService.confirm.and.callFake((config: any) => {
                acceptCallback = config.accept;
            });

            component.resetPreferences();

            expect(confirmationService.confirm).toHaveBeenCalledWith(jasmine.objectContaining({
                message: 'Are you sure?',
                header: 'Confirm',
                icon: 'pi pi-exclamation-triangle',
                acceptLabel: 'Yes',
                rejectLabel: 'No'
            }));

            // Simulate user accepting the confirmation
            if (acceptCallback) {
                acceptCallback();
            }

            expect(component.selectedLanguage()).toBe('en');
            expect(component.isDarkMode()).toBe(false);
            expect(languageService.setLanguage).toHaveBeenCalledWith('en');
        });

        it('should handle translation error and show fallback confirmation', () => {
            translateService.get.and.returnValue(throwError(() => new Error('Translation error')));
            spyOn(console, 'error');

            let acceptCallback: Function | undefined;
            confirmationService.confirm.and.callFake((config: any) => {
                acceptCallback = config.accept;
            });

            component.resetPreferences();

            expect(console.error).toHaveBeenCalledWith('Error loading translations:', jasmine.any(Error));
            expect(confirmationService.confirm).toHaveBeenCalledWith(jasmine.objectContaining({
                message: 'Are you sure you want to reset all preferences to their default values?',
                header: 'Confirm',
                acceptLabel: 'Yes',
                rejectLabel: 'No'
            }));

            // Simulate user accepting the fallback confirmation
            if (acceptCallback) {
                acceptCallback();
            }

            expect(component.selectedLanguage()).toBe('en');
            expect(component.isDarkMode()).toBe(false);
        });

        it('should not reset preferences when user rejects confirmation', () => {
            const translations = {
                'preferences.resetConfirm': 'Are you sure?',
                'preferences.confirmHeader': 'Confirm',
                'common.yes': 'Yes',
                'common.no': 'No'
            };
            translateService.get.and.returnValue(of(translations));

            component.selectedLanguage.set('es');
            component.isDarkMode.set(true);

            confirmationService.confirm.and.callFake(() => {
                // User rejects - accept callback is not called
            });

            component.resetPreferences();

            // Values should remain unchanged
            expect(component.selectedLanguage()).toBe('es');
            expect(component.isDarkMode()).toBe(true);
        });
    });

    describe('showSaveSuccess', () => {
        it('should show success message and hide after timeout', fakeAsync(() => {
            expect(component.saveSuccess()).toBe(false);

            component.showSaveSuccess();

            expect(component.saveSuccess()).toBe(true);

            tick(component['SUCCESS_MESSAGE_DURATION']);

            expect(component.saveSuccess()).toBe(false);
        }));

        it('should use SUCCESS_MESSAGE_DURATION constant', fakeAsync(() => {
            expect(component['SUCCESS_MESSAGE_DURATION']).toBe(3000);

            component.showSaveSuccess();
            expect(component.saveSuccess()).toBe(true);

            tick(2999);
            expect(component.saveSuccess()).toBe(true);

            tick(1);
            expect(component.saveSuccess()).toBe(false);
        }));
    });
});
