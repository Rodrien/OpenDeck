import { Component, OnInit, signal, ViewChild } from '@angular/core';
import { MenuItem } from 'primeng/api';
import { RouterModule, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AvatarModule } from 'primeng/avatar';
import { Menu } from 'primeng/menu';
import { LayoutService } from '../service/layout.service';
import { AuthService } from '../../services/auth.service';
import { User } from '../../models/user.model';

@Component({
    selector: 'app-topbar',
    standalone: true,
    imports: [
        RouterModule,
        CommonModule,
        AvatarModule,
        Menu
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
                <!-- Dark Mode Toggle -->
                <button
                    type="button"
                    class="layout-topbar-action"
                    (click)="toggleDarkMode()"
                    [attr.aria-pressed]="isDarkMode()"
                    [attr.aria-label]="isDarkMode() ? 'Switch to light mode' : 'Switch to dark mode'"
                >
                    <i [class]="isDarkMode() ? 'pi pi-moon' : 'pi pi-sun'"></i>
                </button>

                <!-- User Avatar -->
                <div class="user-avatar-container">
                    <button
                        type="button"
                        class="avatar-button p-0 border-none bg-transparent cursor-pointer"
                        (click)="toggleUserMenu($event)"
                        [attr.aria-label]="'User menu'"
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
    @ViewChild('userMenu', { static: false }) userMenu!: Menu;
    items!: MenuItem[];
    currentUser = signal<User | null>(null);
    userMenuItems: MenuItem[] = [];
    isDarkMode = signal<boolean>(false);

    constructor(
        public layoutService: LayoutService,
        private authService: AuthService,
        private router: Router
    ) {}

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
    }

    ngOnInit(): void {
        // Initialize dark mode from layout service
        this.isDarkMode.set(this.layoutService.isDarkTheme() ?? false);

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

    toggleUserMenu(event: Event) {
        event.stopPropagation();
        if (this.userMenu) {
            this.userMenu.toggle(event);
        } else {
            console.error('userMenu is not defined');
        }
    }

    logout() {
        this.authService.logout();
    }

    navigateToPreferences() {
        this.router.navigate(['/pages/preferences']);
    }
}
