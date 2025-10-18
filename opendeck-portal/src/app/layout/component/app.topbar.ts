import { Component, OnInit, signal, ViewChild } from '@angular/core';
import { MenuItem } from 'primeng/api';
import { RouterModule, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { StyleClassModule } from 'primeng/styleclass';
import { AvatarModule } from 'primeng/avatar';
import { BadgeModule } from 'primeng/badge';
import { Menu } from 'primeng/menu';
import { AppConfigurator } from './app.configurator';
import { LayoutService } from '../service/layout.service';
import { AuthService } from '../../services/auth.service';
import { User } from '../../models/user.model';
import { LanguageSelectorComponent } from '../../components/language-selector/language-selector.component';

@Component({
    selector: 'app-topbar',
    standalone: true,
    imports: [
        RouterModule,
        CommonModule,
        StyleClassModule,
        AvatarModule,
        BadgeModule,
        Menu,
        AppConfigurator,
        LanguageSelectorComponent
    ],
    template: `
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
                <div class="layout-config-menu">
                    <!-- Language Selector -->
                    <app-language-selector></app-language-selector>

                    <!-- Dark Mode Toggle -->
                    <button type="button" class="layout-topbar-action" (click)="toggleDarkMode()">
                        <i [ngClass]="{ 'pi ': true, 'pi-moon': layoutService.isDarkTheme(), 'pi-sun': !layoutService.isDarkTheme() }"></i>
                    </button>

                    <!-- Theme Configurator -->
                    <div class="relative">
                        <button
                            class="layout-topbar-action layout-topbar-action-highlight"
                            pStyleClass="@next"
                            enterFromClass="hidden"
                            enterActiveClass="animate-scalein"
                            leaveToClass="hidden"
                            leaveActiveClass="animate-fadeout"
                            [hideOnOutsideClick]="true"
                        >
                            <i class="pi pi-palette"></i>
                        </button>
                        <app-configurator />
                    </div>
                </div>

                <!-- User Avatar -->
                <div class="user-avatar-container">
                    <button
                        type="button"
                        class="avatar-button p-0 border-none bg-transparent cursor-pointer"
                        (click)="toggleUserMenu($event)"
                        [attr.aria-label]="'User menu'"
                    >
                        <p-avatar
                            [label]="getUserInitials()"
                            styleClass="bg-primary text-white"
                            shape="circle"
                            size="large"
                        ></p-avatar>
                    </button>
                    <p-menu #userMenu [model]="userMenuItems" [popup]="true" styleClass="user-menu">
                        <ng-template pTemplate="start">
                            <div class="user-menu-header">
                                <div class="flex items-center gap-3 p-3 border-bottom-1 surface-border">
                                    <p-avatar
                                        [label]="getUserInitials()"
                                        styleClass="bg-primary text-white"
                                        shape="circle"
                                    ></p-avatar>
                                    <div class="flex flex-col">
                                        <span class="font-semibold text-surface-900 dark:text-surface-0">{{ currentUser()?.name || 'User' }}</span>
                                        <span class="text-muted-color text-sm">{{ currentUser()?.email || 'Not logged in' }}</span>
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
    @ViewChild('userMenu') userMenu!: Menu;
    items!: MenuItem[];
    currentUser = signal<User | null>(null);
    userMenuItems: MenuItem[] = [];

    constructor(
        public layoutService: LayoutService,
        private authService: AuthService,
        private router: Router
    ) {}

    ngOnInit(): void {
        // Subscribe to current user changes
        this.authService.currentUser$.subscribe(user => {
            this.currentUser.set(user);
        });

        // Setup user menu items
        this.userMenuItems = [
            {
                label: 'Preferences',
                icon: 'pi pi-cog',
                command: () => this.navigateToPreferences()
            },
            {
                separator: true
            },
            {
                label: 'Logout',
                icon: 'pi pi-sign-out',
                command: () => this.logout()
            }
        ];
    }

    toggleDarkMode() {
        this.layoutService.layoutConfig.update((state) => ({
            ...state,
            darkTheme: !state.darkTheme
        }));
    }

    toggleUserMenu(event: Event) {
        if (this.userMenu) {
            this.userMenu.toggle(event);
        }
    }

    logout() {
        // Confirm logout
        if (confirm('Are you sure you want to logout?')) {
            this.authService.logout();
        }
    }

    navigateToPreferences() {
        this.router.navigate(['/pages/preferences']);
    }

    /**
     * Get user initials for avatar
     * @returns User initials (e.g., "JD" for John Doe)
     */
    getUserInitials(): string {
        const user = this.currentUser();
        if (!user) return '?';

        if (user.name) {
            // Take first two characters of name
            return user.name.substring(0, 2).toUpperCase();
        }

        if (user.email) {
            // Use first letter of email
            return user.email.charAt(0).toUpperCase();
        }

        return '?';
    }
}
