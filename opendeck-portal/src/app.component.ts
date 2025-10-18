import { Component, OnInit } from '@angular/core';
import { RouterModule } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';

@Component({
    selector: 'app-root',
    standalone: true,
    imports: [RouterModule],
    template: `<router-outlet></router-outlet>`
})
export class AppComponent implements OnInit {
    constructor(private translate: TranslateService) {
        // Set default language
        this.translate.setDefaultLang('en');

        // Try to get saved language preference
        const savedLang = localStorage.getItem('opendeck-language') as 'en' | 'es';
        const browserLang = this.translate.getBrowserLang();

        // Use saved language, or browser language if it's supported, otherwise default to 'en'
        const langToUse = savedLang || (browserLang === 'es' ? 'es' : 'en');
        this.translate.use(langToUse);
    }

    ngOnInit(): void {
        // Additional initialization if needed
    }
}
