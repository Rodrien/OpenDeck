import { Component, DestroyRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MenuItem } from 'primeng/api';
import { AppMenuitem } from './app.menuitem';
import { TranslateService } from '@ngx-translate/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { firstValueFrom } from 'rxjs';

@Component({
    selector: 'app-menu',
    standalone: true,
    imports: [CommonModule, AppMenuitem, RouterModule],
    template: `<ul class="layout-menu">
        <ng-container *ngFor="let item of model; let i = index">
            <li app-menuitem *ngIf="!item.separator" [item]="item" [index]="i" [root]="true"></li>
            <li *ngIf="item.separator" class="menu-separator"></li>
        </ng-container>
    </ul> `
})
export class AppMenu {
    model: MenuItem[] = [];
    private destroyRef = inject(DestroyRef);

    constructor(private translate: TranslateService) {}

    async ngOnInit() {
        // Initialize menu items with translations
        await this.updateMenuItems();

        // Update menu items when language changes
        this.translate.onLangChange
            .pipe(takeUntilDestroyed(this.destroyRef))
            .subscribe(async () => {
                await this.updateMenuItems();
            });
    }

    /**
     * Update menu items with current translations
     */
    private async updateMenuItems(): Promise<void> {
        const translations = await firstValueFrom(
            this.translate.get([
                'menu.main',
                'menu.flashcards',
                'menu.uploadDocuments'
            ])
        );

        this.model = [
            {
                label: translations['menu.main'] || 'Main',
                items: [
                    {
                        label: translations['menu.flashcards'] || 'Flashcards',
                        icon: 'pi pi-fw pi-book',
                        routerLink: ['/pages/flashcards']
                    },
                    {
                        label: translations['menu.uploadDocuments'] || 'Upload Documents',
                        icon: 'pi pi-fw pi-cloud-upload',
                        routerLink: ['/pages/flashcards/upload']
                    }
                ]
            }
        ];
    }
}
