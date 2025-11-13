# AGENTS.md

## Build/Lint/Test Commands

### Backend (FastAPI)
```bash
cd backend
pytest                           # Run all tests
pytest tests/unit/test_file.py    # Run single test file
pytest -k "test_function"         # Run specific test
pytest --cov=app                  # With coverage
black .                           # Format code
ruff check .                      # Lint code
ruff check --fix .                # Auto-fix lint issues
mypy .                            # Type checking
```

### Frontend (Angular)
```bash
cd opendeck-portal
ng test                           # Run all tests
ng test --include="**/*.spec.ts"  # Run specific test pattern
ng build                          # Build for production
ng serve                          # Dev server
npm run format                    # Format with Prettier
ng lint                           # Lint with ESLint
```

## Code Style Guidelines

### Backend (Python)
- **Formatting**: Black (100 char line length)
- **Linting**: Ruff with E, W, F, I, B, C4, UP rules
- **Types**: MyPy strict mode, all functions typed
- **Imports**: isort formatting, no unused imports
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Error Handling**: Use Pydantic for validation, raise HTTPException for API errors

### Frontend (TypeScript/Angular)
- **Components**: Standonly components, no NgModules
- **Formatting**: Prettier (4 spaces, single quotes, 250 char width)
- **Linting**: ESLint with Angular rules, Prettier integration
- **Imports**: Organized with blank lines between groups
- **Naming**: kebab-case for components, camelCase for methods/properties
- **State**: Use Angular Signals, avoid any types
- **UI**: PrimeNG components, TailwindCSS utilities, dark mode support

### General
- All user-facing text must be translated (en.json, es.json)
- Follow clean architecture principles
- Write tests for new features
- Use dependency injection
- Handle loading states and errors gracefully