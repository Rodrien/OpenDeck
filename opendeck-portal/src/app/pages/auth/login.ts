import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { CheckboxModule } from 'primeng/checkbox';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { RippleModule } from 'primeng/ripple';
import { MessageModule } from 'primeng/message';
import { AppFloatingConfigurator } from '../../layout/component/app.floatingconfigurator';
import { AuthService } from '../../services/auth.service';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-login',
    standalone: true,
    imports: [CommonModule, ButtonModule, CheckboxModule, InputTextModule, PasswordModule, FormsModule, RouterModule, RippleModule, AppFloatingConfigurator, MessageModule],
    template: `
        <app-floating-configurator />
        <div class="bg-surface-50 dark:bg-surface-950 flex items-center justify-center min-h-screen min-w-screen overflow-hidden">
            <div class="flex flex-col items-center justify-center">
                <div style="border-radius: 56px; padding: 0.3rem; background: linear-gradient(180deg, var(--primary-color) 10%, rgba(33, 150, 243, 0) 30%)">
                    <div class="w-full bg-surface-0 dark:bg-surface-900 py-20 px-8 sm:px-20" style="border-radius: 53px">
                        <div class="text-center mb-8">
                            <img src="images/opendeck_cards_cropped.png" alt="OpenDeck Logo" class="mb-8 w-64 shrink-0 mx-auto" />
                            <div class="text-surface-900 dark:text-surface-0 text-3xl font-medium mb-4">Welcome to OpenDeck!</div>
                            <span class="text-muted-color font-medium">Sign in to continue</span>
                        </div>

                        <div>
                            @if (errorMessage()) {
                                <p-message severity="error" [text]="errorMessage()" styleClass="mb-4 w-full" />
                            }

                            <label for="username" class="block text-surface-900 dark:text-surface-0 text-xl font-medium mb-2">Username</label>
                            <input
                                pInputText
                                id="username"
                                type="text"
                                placeholder="Enter username"
                                class="w-full md:w-120 mb-6"
                                [(ngModel)]="username"
                                (keyup.enter)="onLogin()"
                            />

                            <label for="password" class="block text-surface-900 dark:text-surface-0 font-medium text-xl mb-2">Password</label>
                            <p-password
                                id="password"
                                [(ngModel)]="password"
                                placeholder="Enter password"
                                [toggleMask]="true"
                                styleClass="mb-4"
                                [fluid]="true"
                                [feedback]="false"
                                (keyup.enter)="onLogin()"
                            ></p-password>

                            <div class="flex items-center justify-between mt-2 mb-8 gap-8">
                                <div class="flex items-center">
                                    <p-checkbox [(ngModel)]="rememberMe" id="rememberme1" binary class="mr-2"></p-checkbox>
                                    <label for="rememberme1">Remember me</label>
                                </div>
                            </div>

                            <p-button
                                label="Sign In"
                                styleClass="w-full"
                                (onClick)="onLogin()"
                                [loading]="isLoading()"
                            ></p-button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
})
export class Login {
    username: string = '';
    password: string = '';
    rememberMe: boolean = false;

    // Signals for reactive state
    errorMessage = signal<string>('');
    isLoading = signal<boolean>(false);

    constructor(
        private authService: AuthService,
        private router: Router
    ) {}

    /**
     * Handle login
     */
    onLogin(): void {
        // Clear previous error
        this.errorMessage.set('');

        // Validate inputs
        if (!this.username || !this.password) {
            this.errorMessage.set('Please enter both username and password');
            return;
        }

        // Set loading state
        this.isLoading.set(true);

        // Simulate async operation
        setTimeout(() => {
            const success = this.authService.login(this.username, this.password);

            if (success) {
                // Redirect to dashboard
                this.router.navigate(['/']);
            } else {
                this.errorMessage.set('Invalid username or password');
            }

            this.isLoading.set(false);
        }, 500);
    }
}
