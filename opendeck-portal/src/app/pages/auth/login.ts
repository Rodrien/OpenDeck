import { Component, signal, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute, RouterModule } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { CheckboxModule } from 'primeng/checkbox';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { RippleModule } from 'primeng/ripple';
import { MessageModule } from 'primeng/message';
import { TranslateModule } from '@ngx-translate/core';
import { AppFloatingConfigurator } from '../../layout/component/app.floatingconfigurator';
import { AuthService } from '../../services/auth.service';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-login',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        ButtonModule,
        CheckboxModule,
        InputTextModule,
        PasswordModule,
        RouterModule,
        RippleModule,
        AppFloatingConfigurator,
        MessageModule,
        TranslateModule
    ],
    template: `
        <app-floating-configurator />
        <div class="bg-surface-50 dark:bg-surface-950 flex items-center justify-center min-h-screen min-w-screen overflow-hidden">
            <div class="flex flex-col items-center justify-center">
                <div style="border-radius: 56px; padding: 0.3rem; background: linear-gradient(180deg, var(--primary-color) 10%, rgba(33, 150, 243, 0) 30%)">
                    <div class="w-full bg-surface-0 dark:bg-surface-900 py-20 px-8 sm:px-20" style="border-radius: 53px">
                        <div class="text-center mb-8">
                            <img src="images/opendeck_cards_cropped.png" alt="OpenDeck Logo" class="mb-8 w-64 shrink-0 mx-auto" />
                            <div class="text-surface-900 dark:text-surface-0 text-3xl font-medium mb-4">{{ 'auth.welcomeToOpenDeck' | translate }}</div>
                            <span class="text-muted-color font-medium">{{ 'auth.signInToContinue' | translate }}</span>
                        </div>

                        <form [formGroup]="loginForm" (ngSubmit)="onSubmit()">
                            @if (errorMessage()) {
                                <p-message severity="error" [text]="errorMessage()" styleClass="mb-4 w-full" />
                            }

                            <label for="email" class="block text-surface-900 dark:text-surface-0 text-xl font-medium mb-2">{{ 'auth.email' | translate }}</label>
                            <input
                                pInputText
                                id="email"
                                type="email"
                                [placeholder]="'auth.enterEmail' | translate"
                                class="w-full md:w-120 mb-2"
                                formControlName="email"
                                [class.ng-invalid]="loginForm.get('email')?.invalid && loginForm.get('email')?.touched"
                                [class.ng-dirty]="loginForm.get('email')?.touched"
                            />
                            @if (loginForm.get('email')?.invalid && loginForm.get('email')?.touched) {
                                <small class="block text-red-500 mb-4">
                                    @if (loginForm.get('email')?.errors?.['required']) {
                                        {{ 'auth.emailRequired' | translate }}
                                    }
                                    @if (loginForm.get('email')?.errors?.['email']) {
                                        {{ 'auth.emailInvalid' | translate }}
                                    }
                                </small>
                            } @else {
                                <div class="mb-4"></div>
                            }

                            <label for="password" class="block text-surface-900 dark:text-surface-0 font-medium text-xl mb-2">{{ 'auth.password' | translate }}</label>
                            <p-password
                                id="password"
                                [placeholder]="'auth.enterPassword' | translate"
                                [toggleMask]="true"
                                styleClass="mb-2"
                                [fluid]="true"
                                [feedback]="false"
                                formControlName="password"
                                [class.ng-invalid]="loginForm.get('password')?.invalid && loginForm.get('password')?.touched"
                                [class.ng-dirty]="loginForm.get('password')?.touched"
                            ></p-password>
                            @if (loginForm.get('password')?.invalid && loginForm.get('password')?.touched) {
                                <small class="block text-red-500 mb-4">{{ 'auth.passwordRequired' | translate }}</small>
                            } @else {
                                <div class="mb-4"></div>
                            }

                            <div class="flex items-center justify-between mt-2 mb-8 gap-8">
                                <div class="flex items-center">
                                    <p-checkbox formControlName="rememberMe" id="rememberme1" binary class="mr-2"></p-checkbox>
                                    <label for="rememberme1" class="text-surface-900 dark:text-surface-0">{{ 'auth.rememberMe' | translate }}</label>
                                </div>
                            </div>

                            <p-button
                                [label]="'auth.loginButton' | translate"
                                styleClass="w-full"
                                type="submit"
                                [loading]="isLoading()"
                                [disabled]="loginForm.invalid"
                            ></p-button>

                            <div class="text-center mt-6">
                                <span class="text-muted-color">{{ 'auth.noAccount' | translate }} </span>
                                <a routerLink="/auth/register" class="text-primary font-medium hover:underline">{{ 'auth.signUp' | translate }}</a>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    `
})
export class Login implements OnInit {
    loginForm!: FormGroup;

    // Signals for reactive state
    errorMessage = signal<string>('');
    isLoading = signal<boolean>(false);

    private returnUrl: string = '/';

    constructor(
        private fb: FormBuilder,
        private authService: AuthService,
        private router: Router,
        private route: ActivatedRoute
    ) {}

    ngOnInit(): void {
        // Initialize the form with validators
        this.loginForm = this.fb.group({
            email: ['', [Validators.required, Validators.email]],
            password: ['', Validators.required],
            rememberMe: [false]
        });

        // Get return URL from route parameters or default to '/'
        this.returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/';
    }

    /**
     * Handle login form submission
     */
    onSubmit(): void {
        // Clear previous error
        this.errorMessage.set('');

        // Mark all fields as touched to trigger validation messages
        if (this.loginForm.invalid) {
            Object.keys(this.loginForm.controls).forEach(key => {
                this.loginForm.get(key)?.markAsTouched();
            });
            return;
        }

        // Set loading state
        this.isLoading.set(true);

        const { email, password } = this.loginForm.value;

        // Call AuthService login
        this.authService.login(email, password).subscribe({
            next: (response) => {
                this.isLoading.set(false);
                // Navigate to return URL or dashboard
                this.router.navigate([this.returnUrl]);
            },
            error: (error) => {
                this.isLoading.set(false);
                this.errorMessage.set(error.message || 'Invalid email or password');
                console.error('Login error:', error);
            }
        });
    }
}
