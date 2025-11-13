import { Component, signal, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, AbstractControl, ValidationErrors } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { RippleModule } from 'primeng/ripple';
import { MessageModule } from 'primeng/message';
import { DividerModule } from 'primeng/divider';
import { AppFloatingConfigurator } from '../../layout/component/app.floatingconfigurator';
import { AuthService } from '../../services/auth.service';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-register',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        ButtonModule,
        InputTextModule,
        PasswordModule,
        RouterModule,
        RippleModule,
        AppFloatingConfigurator,
        MessageModule,
        DividerModule
    ],
    template: `
        <app-floating-configurator />
        <div class="bg-surface-50 dark:bg-surface-950 flex items-center justify-center min-h-screen min-w-screen overflow-hidden">
            <div class="flex flex-col items-center justify-center">
                <div style="border-radius: 56px; padding: 0.3rem; background: linear-gradient(180deg, var(--primary-color) 10%, rgba(33, 150, 243, 0) 30%)">
                    <div class="w-full bg-surface-0 dark:bg-surface-900 py-20 px-8 sm:px-20" style="border-radius: 53px">
                        <div class="text-center mb-8">
                            <img src="images/opendeck_cards_cropped.png" alt="OpenDeck Logo" class="mb-8 w-64 shrink-0 mx-auto" />
                            <div class="text-surface-900 dark:text-surface-0 text-3xl font-medium mb-4">Join OpenDeck</div>
                            <span class="text-muted-color font-medium">Create your account to get started</span>
                        </div>

                        <form [formGroup]="registerForm" (ngSubmit)="onSubmit()">
                            @if (errorMessage()) {
                                <p-message severity="error" [text]="errorMessage()" styleClass="mb-4 w-full" />
                            }

                            <label for="email" class="block text-surface-900 dark:text-surface-0 text-xl font-medium mb-2">Email</label>
                            <input
                                pInputText
                                id="email"
                                type="email"
                                placeholder="Enter your email"
                                class="w-full md:w-120 mb-2"
                                formControlName="email"
                                [class.ng-invalid]="registerForm.get('email')?.invalid && registerForm.get('email')?.touched"
                                [class.ng-dirty]="registerForm.get('email')?.touched"
                            />
                            @if (registerForm.get('email')?.invalid && registerForm.get('email')?.touched) {
                                <small class="block text-red-500 mb-4">
                                    @if (registerForm.get('email')?.errors?.['required']) {
                                        Email is required
                                    }
                                    @if (registerForm.get('email')?.errors?.['email']) {
                                        Please enter a valid email address
                                    }
                                </small>
                            } @else {
                                <div class="mb-4"></div>
                            }

                            <label for="username" class="block text-surface-900 dark:text-surface-0 text-xl font-medium mb-2">Username</label>
                            <input
                                pInputText
                                id="username"
                                type="text"
                                placeholder="Choose a username"
                                class="w-full md:w-120 mb-2"
                                formControlName="username"
                                [class.ng-invalid]="registerForm.get('username')?.invalid && registerForm.get('username')?.touched"
                                [class.ng-dirty]="registerForm.get('username')?.touched"
                            />
                            @if (registerForm.get('username')?.invalid && registerForm.get('username')?.touched) {
                                <small class="block text-red-500 mb-4">
                                    @if (registerForm.get('username')?.errors?.['required']) {
                                        Username is required
                                    }
                                    @if (registerForm.get('username')?.errors?.['minlength']) {
                                        Username must be at least 3 characters
                                    }
                                </small>
                            } @else {
                                <div class="mb-4"></div>
                            }

                            <label for="password" class="block text-surface-900 dark:text-surface-0 font-medium text-xl mb-2">Password</label>
                            <p-password
                                id="password"
                                placeholder="Create a password"
                                [toggleMask]="true"
                                styleClass="mb-2"
                                [fluid]="true"
                                [feedback]="true"
                                formControlName="password"
                                [class.ng-invalid]="registerForm.get('password')?.invalid && registerForm.get('password')?.touched"
                                [class.ng-dirty]="registerForm.get('password')?.touched"
                            >
                                <ng-template pTemplate="footer">
                                    <p class="mt-2 text-sm text-muted-color">Password must be at least 8 characters long</p>
                                </ng-template>
                            </p-password>
                            @if (registerForm.get('password')?.invalid && registerForm.get('password')?.touched) {
                                <small class="block text-red-500 mb-4">
                                    @if (registerForm.get('password')?.errors?.['required']) {
                                        Password is required
                                    }
                                    @if (registerForm.get('password')?.errors?.['minlength']) {
                                        Password must be at least 8 characters
                                    }
                                </small>
                            } @else {
                                <div class="mb-4"></div>
                            }

                            <label for="confirmPassword" class="block text-surface-900 dark:text-surface-0 font-medium text-xl mb-2">Confirm Password</label>
                            <p-password
                                id="confirmPassword"
                                placeholder="Confirm your password"
                                [toggleMask]="true"
                                styleClass="mb-2"
                                [fluid]="true"
                                [feedback]="false"
                                formControlName="confirmPassword"
                                [class.ng-invalid]="registerForm.get('confirmPassword')?.invalid && registerForm.get('confirmPassword')?.touched"
                                [class.ng-dirty]="registerForm.get('confirmPassword')?.touched"
                            ></p-password>
                            @if (registerForm.get('confirmPassword')?.invalid && registerForm.get('confirmPassword')?.touched) {
                                <small class="block text-red-500 mb-4">
                                    @if (registerForm.get('confirmPassword')?.errors?.['required']) {
                                        Please confirm your password
                                    }
                                </small>
                            } @else if (registerForm.errors?.['passwordMismatch'] && registerForm.get('confirmPassword')?.touched) {
                                <small class="block text-red-500 mb-4">Passwords do not match</small>
                            } @else {
                                <div class="mb-4"></div>
                            }

                            <p-button
                                label="Create Account"
                                styleClass="w-full mt-4"
                                type="submit"
                                [loading]="isLoading()"
                                [disabled]="registerForm.invalid"
                            ></p-button>

                            <p-divider align="center" class="my-6">
                                <span class="text-muted-color text-sm">OR</span>
                            </p-divider>

                            <p-button
                                label="Sign up with Google"
                                icon="pi pi-google"
                                styleClass="w-full"
                                severity="secondary"
                                outlined="true"
                                [loading]="isLoading()"
                                (click)="signInWithGoogle()"
                            ></p-button>

                            <div class="text-center mt-6">
                                <span class="text-muted-color">Already have an account? </span>
                                <a routerLink="/auth/login" class="text-primary font-medium hover:underline">Sign in</a>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    `
})
export class Register implements OnInit {
    registerForm!: FormGroup;

    // Signals for reactive state
    errorMessage = signal<string>('');
    isLoading = signal<boolean>(false);

    constructor(
        private fb: FormBuilder,
        private authService: AuthService,
        private router: Router
    ) {}

    ngOnInit(): void {
        // Initialize the form with validators
        this.registerForm = this.fb.group({
            email: ['', [Validators.required, Validators.email]],
            username: ['', [Validators.required, Validators.minLength(3)]],
            password: ['', [Validators.required, Validators.minLength(8)]],
            confirmPassword: ['', Validators.required]
        }, {
            validators: this.passwordMatchValidator
        });
    }

    /**
     * Custom validator to check if passwords match
     */
    passwordMatchValidator(control: AbstractControl): ValidationErrors | null {
        const password = control.get('password');
        const confirmPassword = control.get('confirmPassword');

        if (!password || !confirmPassword) {
            return null;
        }

        return password.value === confirmPassword.value ? null : { passwordMismatch: true };
    }

    /**
     * Handle registration form submission
     */
    onSubmit(): void {
        // Clear previous error
        this.errorMessage.set('');

        // Mark all fields as touched to trigger validation messages
        if (this.registerForm.invalid) {
            Object.keys(this.registerForm.controls).forEach(key => {
                this.registerForm.get(key)?.markAsTouched();
            });
            return;
        }

        // Set loading state
        this.isLoading.set(true);

        const { email, username, password } = this.registerForm.value;

        // Call AuthService register
        this.authService.register(email, username, password).subscribe({
            next: (response) => {
                this.isLoading.set(false);
                // Automatically logged in after registration, navigate to dashboard
                this.router.navigate(['/']);
            },
            error: (error) => {
                this.isLoading.set(false);
                this.errorMessage.set(error.message || 'Registration failed. Please try again.');
                console.error('Registration error:', error);
            }
        });
    }

    /**
     * Handle Google Sign-In for registration
     */
    signInWithGoogle(): void {
        this.isLoading.set(true);
        this.errorMessage.set('');

        this.authService.loginWithGoogle();
    }
}
