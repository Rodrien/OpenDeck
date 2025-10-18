import { Component, OnInit, signal } from '@angular/core';
import { MenuItem } from 'primeng/api';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { StyleClassModule } from 'primeng/styleclass';
import { AvatarModule } from 'primeng/avatar';
import { BadgeModule } from 'primeng/badge';
import { AppConfigurator } from './app.configurator';
import { LayoutService } from '../service/layout.service';
import { AuthService } from '../../services/auth.service';
import { User } from '../../models/user.model';

@Component({
    selector: 'app-topbar',
    standalone: true,
    imports: [
        RouterModule,
        CommonModule,
        StyleClassModule,
        AvatarModule,
        BadgeModule,
        AppConfigurator
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
                    <button type="button" class="layout-topbar-action" (click)="toggleDarkMode()">
                        <i [ngClass]="{ 'pi ': true, 'pi-moon': layoutService.isDarkTheme(), 'pi-sun': !layoutService.isDarkTheme() }"></i>
                    </button>
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

                @if (currentUser()) {
                    <button
                        class="layout-topbar-menu-button layout-topbar-action"
                        pStyleClass="@next"
                        enterFromClass="hidden"
                        enterActiveClass="animate-scalein"
                        leaveToClass="hidden"
                        leaveActiveClass="animate-fadeout"
                        [hideOnOutsideClick]="true"
                    >
                        <i class="pi pi-user"></i>
                    </button>

                    <div class="layout-topbar-menu hidden lg:flex">
                        <div class="layout-topbar-menu-content flex items-center gap-4">
                            <div class="flex flex-col items-end text-sm">
                                <span class="font-semibold text-surface-900 dark:text-surface-0">{{ currentUser()?.username }}</span>
                                <span class="text-muted-color text-xs">{{ currentUser()?.email }}</span>
                            </div>
                            <p-avatar
                                [label]="getUserInitials()"
                                styleClass="bg-primary text-white"
                                shape="circle"
                            ></p-avatar>
                            <button
                                type="button"
                                class="layout-topbar-action ml-2"
                                (click)="logout()"
                                title="Logout"
                            >
                                <i class="pi pi-sign-out"></i>
                            </button>
                        </div>
                    </div>

                    <!-- Mobile menu -->
                    <div class="layout-topbar-menu lg:hidden">
                        <div class="layout-topbar-menu-content">
                            <div class="flex flex-col p-4 gap-3">
                                <div class="flex items-center gap-3 mb-2">
                                    <p-avatar
                                        [label]="getUserInitials()"
                                        styleClass="bg-primary text-white"
                                        shape="circle"
                                    ></p-avatar>
                                    <div class="flex flex-col text-sm">
                                        <span class="font-semibold text-surface-900 dark:text-surface-0">{{ currentUser()?.username }}</span>
                                        <span class="text-muted-color text-xs">{{ currentUser()?.email }}</span>
                                    </div>
                                </div>
                                <button
                                    type="button"
                                    class="layout-topbar-action w-full justify-start"
                                    (click)="logout()"
                                >
                                    <i class="pi pi-sign-out mr-2"></i>
                                    <span>Logout</span>
                                </button>
                            </div>
                        </div>
                    </div>
                }
            </div>
        </div>
    `
})
export class AppTopbar implements OnInit {
    items!: MenuItem[];
    currentUser = signal<User | null>(null);

    constructor(
        public layoutService: LayoutService,
        private authService: AuthService
    ) {}

    ngOnInit(): void {
        // Subscribe to current user changes
        this.authService.currentUser$.subscribe(user => {
            this.currentUser.set(user);
        });
    }

    toggleDarkMode() {
        this.layoutService.layoutConfig.update((state) => ({
            ...state,
            darkTheme: !state.darkTheme
        }));
    }

    logout() {
        // Confirm logout
        if (confirm('Are you sure you want to logout?')) {
            this.authService.logout();
        }
    }

    /**
     * Get user initials for avatar
     * @returns User initials (e.g., "JD" for John Doe)
     */
    getUserInitials(): string {
        const user = this.currentUser();
        if (!user) return '?';

        if (user.username) {
            // Take first two characters of username
            return user.username.substring(0, 2).toUpperCase();
        }

        if (user.email) {
            // Use first letter of email
            return user.email.charAt(0).toUpperCase();
        }

        return '?';
    }
}
