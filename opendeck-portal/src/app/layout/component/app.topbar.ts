import { Component, OnInit, signal, ViewChild, DestroyRef, inject } from '@angular/core';
import { MenuItem, ConfirmationService } from 'primeng/api';
import { RouterModule, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AvatarModule } from 'primeng/avatar';
import { Menu } from 'primeng/menu';
import { ConfirmDialog } from 'primeng/confirmdialog';
import { LayoutService } from '../service/layout.service';
import { AuthService } from '../../services/auth.service';
import { User } from '../../models/user.model';
import { TranslateService, LangChangeEvent } from '@ngx-translate/core';
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
        AvatarModule,
        Menu,
        ConfirmDialog,
        NotificationBellComponent
    ],
    providers: [ConfirmationService],
    template: `
        <p-confirmDialog />
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
                        <p-avatar
                            icon="pi pi-user"
                            styleClass="bg-primary text-white"
                            shape="circle"
                            size="large"
                        ></p-avatar>
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

    private destroyRef = inject(DestroyRef);

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

        // Initialize menu items
        this.updateUserMenuItems();

        // Update menu items and translations when language changes
        this.translate.onLangChange
            .pipe(takeUntilDestroyed(this.destroyRef))
            .subscribe(() => {
                this.updateTranslations();
                this.updateUserMenuItems();
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
                'topbar.notLoggedIn'
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
}
