import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Select } from 'primeng/select';
import { LanguageService, SupportedLanguage, LanguageOption } from '../../services/language.service';

@Component({
    selector: 'app-language-selector',
    standalone: true,
    imports: [CommonModule, FormsModule, Select],
    template: `
        <p-select
            [options]="languages"
            [(ngModel)]="selectedLanguage"
            (onChange)="onLanguageChange($event)"
            optionLabel="label"
            optionValue="code"
            [style]="{'min-width': '140px'}"
            styleClass="language-select"
        >
            <ng-template let-option pTemplate="item">
                <div class="flex items-center gap-2">
                    <span class="text-lg">{{ option.flag }}</span>
                    <span>{{ option.label }}</span>
                </div>
            </ng-template>
            <ng-template let-option pTemplate="selectedItem">
                <div class="flex items-center gap-2">
                    <span class="text-lg">{{ option.flag }}</span>
                    <span>{{ option.label }}</span>
                </div>
            </ng-template>
        </p-select>
    `,
    styles: [`
        :host ::ng-deep {
            .language-select {
                .p-select {
                    background: transparent;
                    border: 1px solid var(--surface-border);

                    &:hover {
                        border-color: var(--primary-color);
                    }
                }

                .p-select-label {
                    padding: 0.5rem 0.75rem;
                }

                .p-select-trigger {
                    width: 2rem;
                }
            }
        }
    `]
})
export class LanguageSelectorComponent implements OnInit {
    languages: LanguageOption[] = [];
    selectedLanguage: SupportedLanguage = 'en';

    constructor(private languageService: LanguageService) {}

    ngOnInit(): void {
        this.languages = this.languageService.availableLanguages;

        // Subscribe to language changes
        this.languageService.getCurrentLanguage().subscribe(lang => {
            this.selectedLanguage = lang;
        });
    }

    onLanguageChange(event: any): void {
        this.languageService.setLanguage(event.value);
    }
}
