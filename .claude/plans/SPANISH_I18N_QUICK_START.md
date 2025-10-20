# Spanish Localization - Quick Start Guide

**Quick Reference for implementing Spanish translations in OpenDeck**

## TL;DR

1. Install: `npm install @ngx-translate/core @ngx-translate/http-loader`
2. Create: `src/assets/i18n/en.json` and `src/assets/i18n/es.json`
3. Update templates: Replace text with `{{ 'key.name' | translate }}`
4. Add language selector to topbar
5. Deploy (same as before - no changes!)

## What Gets Translated?

✅ **UI Elements** - Buttons, labels, menus, messages
✅ **Form Fields** - Placeholders, validation messages
✅ **Navigation** - Menu items, breadcrumbs
✅ **Error Messages** - All user-facing errors

❌ **Flashcard Content** - Cards stay in original language (by design)
❌ **User Data** - Names, emails, etc.
❌ **Backend** - No API changes needed!

## Implementation Checklist

### Phase 1: Setup (Day 1)
- [ ] Install ngx-translate packages
- [ ] Configure TranslateModule in app.config.ts
- [ ] Create `src/assets/i18n/` folder
- [ ] Create empty `en.json` and `es.json` files

### Phase 2: Infrastructure (Days 2-4)
- [ ] Create LanguageService
- [ ] Create LanguageSelectorComponent
- [ ] Add language detection (localStorage + browser)
- [ ] Test language switching

### Phase 3: Translation Files (Days 5-10)
- [ ] Map out all UI text
- [ ] Create English keys in en.json
- [ ] Copy structure to es.json
- [ ] Get Spanish translations
- [ ] Organize by feature (auth, deck, flashcard, common)

### Phase 4: Template Updates (Week 2-3)
- [ ] Update auth pages
- [ ] Update flashcard viewer
- [ ] Update deck list
- [ ] Update navigation/layout
- [ ] Update common components

### Phase 5: Integration (Week 3-4)
- [ ] Add language selector to topbar
- [ ] Add language option to user menu
- [ ] Update error messages in services
- [ ] Test all flows in both languages

### Phase 6: Testing & Launch (Week 4-5)
- [ ] Manual testing (all pages, both languages)
- [ ] Translation coverage check
- [ ] Fix any missing keys
- [ ] Deploy to production

## File Structure

```
src/
├── assets/
│   └── i18n/
│       ├── en.json          # English translations
│       └── es.json          # Spanish translations
└── app/
    ├── services/
    │   └── language.service.ts
    └── components/
        └── language-selector/
            ├── language-selector.component.ts
            └── language-selector.component.html
```

## Code Examples

### Using Translate Pipe in Templates

```html
<!-- Simple text -->
<h1>{{ 'deck.myDecks' | translate }}</h1>

<!-- With parameters -->
<p>{{ 'deck.cardCount' | translate: {count: deckCount} }}</p>

<!-- In attributes -->
<input [placeholder]="'common.search' | translate">
```

### Using TranslateService in Components

```typescript
import { TranslateService } from '@ngx-translate/core';

constructor(private translate: TranslateService) {}

// Get translation synchronously
const message = this.translate.instant('deck.createNew');

// Get translation asynchronously
this.translate.get('deck.createNew').subscribe(text => {
  console.log(text);
});

// With parameters
const msg = this.translate.instant('deck.cardCount', { count: 5 });
```

## Translation File Example

```json
{
  "auth": {
    "login": "Login",
    "email": "Email",
    "password": "Password"
  },
  "deck": {
    "myDecks": "My Flashcard Decks",
    "createNew": "Create New Deck",
    "cardCount": "{{count}} cards"
  },
  "common": {
    "save": "Save",
    "cancel": "Cancel",
    "search": "Search"
  }
}
```

## Common Patterns

### Conditional Text

```typescript
// In component
get welcomeMessage(): string {
  const hour = new Date().getHours();
  if (hour < 12) return this.translate.instant('common.goodMorning');
  if (hour < 18) return this.translate.instant('common.goodAfternoon');
  return this.translate.instant('common.goodEvening');
}
```

### Confirmation Dialogs

```typescript
deleteCard(cardId: string) {
  const confirmMsg = this.translate.instant('flashcard.deleteConfirm');
  if (confirm(confirmMsg)) {
    this.cardService.delete(cardId);
  }
}
```

### Error Handling

```typescript
private handleError(error: HttpErrorResponse): Observable<never> {
  let errorKey = 'errors.unknown';

  if (error.status === 404) errorKey = 'errors.notFound';
  if (error.status === 500) errorKey = 'errors.serverError';

  const errorMessage = this.translate.instant(errorKey);
  return throwError(() => new Error(errorMessage));
}
```

## Testing Checklist

### Manual Testing
- [ ] Switch language - UI updates immediately
- [ ] Refresh page - selected language persists
- [ ] All text visible (no missing translation keys)
- [ ] Parameters work (e.g., "5 cards" shows "5 tarjetas")
- [ ] Error messages display in correct language
- [ ] Date/number formatting looks correct

### Validation Script
```bash
# Check for missing Spanish translations
node scripts/check-translations.js
```

## Deployment

No changes needed! Deploy exactly as before:

```bash
# Build
npm run build

# Deploy to AWS
aws s3 sync dist/opendeck-portal/browser s3://opendeck-bucket/
aws cloudfront create-invalidation --distribution-id YOUR_ID --paths "/*"
```

Both languages work from the same build! 🎉

## Troubleshooting

### Translation not showing
1. Check key exists in both en.json and es.json
2. Verify TranslateModule is imported in component
3. Check browser console for errors
4. Verify translation files are in `assets/i18n/`

### Language not persisting
1. Check localStorage is working
2. Verify LanguageService sets language on init
3. Check browser localStorage for 'opendeck-language' key

### Missing translation warnings
1. Add missing key to en.json
2. Copy to es.json
3. Translate Spanish value
4. Rebuild app

## Resources

- ngx-translate docs: https://github.com/ngx-translate/core
- Full implementation plan: `SPANISH_LOCALIZATION_PLAN.md`
- Translation glossary: See plan document

## Quick Commands

```bash
# Install dependencies
npm install @ngx-translate/core @ngx-translate/http-loader

# Development
npm start

# Build production
npm run build

# Check translation coverage (after creating script)
npm run check-translations
```

## Need Help?

See the full plan in `SPANISH_LOCALIZATION_PLAN.md` for:
- Complete code examples
- Component implementations
- Translation glossary
- Testing strategies
- Common issues and solutions
