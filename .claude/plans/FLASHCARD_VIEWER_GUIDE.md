# OpenDeck Flashcard Viewer - Quick Start Guide

## Component Structure

```
opendeck-portal/
└── src/
    └── app/
        └── pages/
            └── flashcards/
                ├── models/
                │   ├── deck.interface.ts              # Deck data structure
                │   └── flashcard-data.interface.ts    # Flashcard data structure ✨ NEW
                ├── flashcard-decks-list.component.ts  # Deck listing (existing)
                ├── flashcard-decks-list.component.html
                ├── flashcard-decks-list.component.scss
                ├── flashcard-viewer.component.ts      # Flashcard viewer ✨ NEW
                ├── flashcard-viewer.component.html    # ✨ NEW
                └── flashcard-viewer.component.scss    # ✨ NEW
```

## Navigation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  Deck Listing Component                                         │
│  Route: /pages/flashcards                                       │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   Deck 1    │  │   Deck 2    │  │   Deck 3    │           │
│  │  CS Basics  │  │  Chemistry  │  │  Calculus   │           │
│  │  25 cards   │  │  30 cards   │  │  28 cards   │           │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘           │
│         │ Click          │ Click          │ Click              │
└─────────┼────────────────┼────────────────┼────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Flashcard Viewer Component                                     │
│  Route: /pages/flashcards/viewer/:deckId                       │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Progress Bar: ████████░░░░░░░░░░░░ 40%                 │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  ┌───────────┐                                          │  │
│  │  │ Question  │                                          │  │
│  │  └───────────┘                                          │  │
│  │                                                           │  │
│  │  What is an algorithm?                                   │  │
│  │                                                           │  │
│  │  ─────────────────────────────────                      │  │
│  │                                                           │  │
│  │  ┌──────────┐                                           │  │
│  │  │ Answer   │                                           │  │
│  │  └──────────┘                                           │  │
│  │                                                           │  │
│  │  An algorithm is a step-by-step procedure...           │  │
│  │                                                           │  │
│  │  ┌───────────────────────────────────────────────────┐ │  │
│  │  │ 📄 SOURCE REFERENCE                               │ │  │
│  │  │ Introduction_to_CS_Lecture_01.pdf                 │ │  │
│  │  │ Page 12, Section 2.1                       [🔗]   │ │  │
│  │  └───────────────────────────────────────────────────┘ │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────┐    Card 1 of 25    ┌──────────┐                │
│  │ Previous │                     │   Next   │                │
│  └──────────┘                     └──────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. **Source Attribution** (Critical OpenDeck Requirement)
Every flashcard displays the source document and location in a prominent box:
- Document icon for visual recognition
- Clear "SOURCE REFERENCE" label
- Full citation (document name, page, section)
- Optional external link to source

### 2. **Navigation**
- **Previous/Next Buttons**: Navigate between cards
- **Keyboard Shortcuts**:
  - `←` Previous
  - `→` Next
  - `Space/Enter` Toggle answer
  - `Esc` Back to decks
- **Progress Bar**: Visual progress indicator
- **Card Counter**: Text display (e.g., "1 of 25")

### 3. **Animations**
- **Card Slide**: Smooth transitions when navigating
- **Answer Reveal**: Fade-in effect
- **Hover Effects**: Button and card elevation

### 4. **Responsive Design**
- Desktop: Full layout with keyboard hints
- Tablet: Adjusted spacing and element order
- Mobile: Compact layout, touch-optimized

## Component Inputs/Outputs

### FlashcardViewerComponent

**Route Parameters:**
- `deckId` - The ID of the deck to display

**Internal State (Signals):**
- `deckTitle` - Current deck name
- `cards` - Array of flashcards
- `currentIndex` - Current card position (0-based)
- `showAnswer` - Answer visibility toggle

**Computed Values:**
- `currentCard` - Currently displayed card
- `progress` - Progress percentage (0-100)
- `isFirstCard` - Whether viewing first card
- `isLastCard` - Whether viewing last card
- `cardCountText` - Formatted counter text

## Usage Example

### From Deck Listing Component

```typescript
// In flashcard-decks-list.component.ts
onDeckSelect(deck: Deck): void {
    this.router.navigate(['/pages/flashcards/viewer', deck.id]);
}
```

### Direct Navigation

```typescript
// Navigate to specific deck
this.router.navigate(['/pages/flashcards/viewer', 1]); // CS deck
this.router.navigate(['/pages/flashcards/viewer', 2]); // Chemistry deck
```

## Mock Data Structure

Each deck contains flashcards with the following structure:

```typescript
{
    id: 1,
    question: "What is an algorithm?",
    answer: "An algorithm is a step-by-step procedure...",
    source: "Introduction_to_CS_Lecture_01.pdf - Page 12, Section 2.1",
    sourceUrl: "#" // Optional - link to actual document
}
```

## Available Decks (Mock Data)

1. **ID: 1** - Introduction to Computer Science (5 cards)
2. **ID: 2** - Organic Chemistry Basics (3 cards)
3. **ID: 3** - Calculus I: Derivatives (2 cards)
4. **ID: 4** - World History: Ancient Civilizations (2 cards)
5. **ID: 5** - Microeconomics Principles (2 cards)
6. **ID: 6** - Data Structures & Algorithms (2 cards)

## Styling Customization

### Dark Mode Colors

```scss
// Primary backgrounds
$bg-primary: #1a1a2e to #16213e (gradient)
$bg-card: #2d2d3f to #252535 (gradient)

// Accent colors
$accent-blue: #3b82f6
$accent-indigo: #6366f1

// Text colors
$text-primary: #f5f5f5
$text-secondary: #e0e0e0
$text-muted: #9ca3af

// Source attribution box
$source-bg: rgba(59, 130, 246, 0.08) to rgba(99, 102, 241, 0.08) (gradient)
$source-border: rgba(59, 130, 246, 0.2)
```

### PrimeNG Component Overrides

The component includes deep style overrides for:
- Progress Bar styling
- Button appearances (raised, outlined, text)
- Card elevation and shadows
- Tag colors and gradients

## Accessibility Features

- **ARIA Labels**: All interactive elements properly labeled
- **Keyboard Navigation**: Full keyboard support
- **Focus Indicators**: Visible focus outlines
- **Screen Reader Support**: Semantic HTML
- **Reduced Motion**: Respects user preferences
- **High Contrast**: Enhanced visibility in high contrast mode

## Testing the Component

### 1. Start Development Server
```bash
cd /Users/kike/Repos/OpenDeck/opendeck-portal
npm start
```

### 2. Navigate to Flashcards
Open browser to: `http://localhost:4200/pages/flashcards`

### 3. Select a Deck
Click any deck card to open the viewer

### 4. Test Navigation
- Click Previous/Next buttons
- Use keyboard arrows
- Check progress bar updates
- Verify disabled states on first/last cards

### 5. Test Answer Toggle
- Click "Show Answer" button
- Press Space or Enter
- Verify answer fades in
- Verify source attribution appears

### 6. Test Responsive Design
- Resize browser window
- Check mobile breakpoints (< 640px)
- Check tablet breakpoints (< 768px)
- Verify layout adjustments

## Keyboard Shortcuts Reference

| Key | Action |
|-----|--------|
| `←` | Previous Card |
| `→` | Next Card |
| `Space` | Toggle Answer |
| `Enter` | Toggle Answer |
| `Esc` | Back to Decks |

## Common Customizations

### 1. Change Animation Speed
```scss
// In flashcard-viewer.component.scss
transition: all 0.3s ease; // Change 0.3s to desired duration
```

### 2. Adjust Card Height
```scss
.flashcard-content {
    min-height: 500px; // Change to desired height
}
```

### 3. Modify Source Box Styling
```scss
.source-attribution-box {
    padding: 1.25rem; // Adjust padding
    background: /* custom gradient */;
    border: /* custom border */;
}
```

### 4. Update Progress Bar Colors
```scss
.p-progressbar-value {
    background: linear-gradient(90deg, #custom1 0%, #custom2 100%);
}
```

## Integration with Real Data

To integrate with actual API/service:

1. **Create Flashcard Service**
```typescript
// flashcard.service.ts
export class FlashcardService {
    getDeckById(id: number): Observable<DeckWithCards> {
        return this.http.get(`/api/decks/${id}`);
    }
}
```

2. **Update Component**
```typescript
// In flashcard-viewer.component.ts
private loadDeckData(deckId: number): void {
    this.flashcardService.getDeckById(deckId).subscribe(deck => {
        this.deckTitle.set(deck.title);
        this.cards.set(deck.cards);
    });
}
```

## Troubleshooting

### Issue: Cards not loading
- Verify route parameter is correct
- Check browser console for errors
- Verify mock data includes the deck ID

### Issue: Navigation buttons not working
- Check if currentIndex is updating
- Verify isFirstCard/isLastCard computed values
- Check browser console for errors

### Issue: Animations not smooth
- Check if Angular animations module is imported
- Verify trigger is updating correctly
- Check for CSS conflicts

### Issue: Keyboard shortcuts not working
- Verify HostListener is correctly bound
- Check if another component is capturing events
- Verify focus is not trapped elsewhere

## Next Development Steps

1. **Add Flip Animation**: Implement 3D card flip effect
2. **Study Mode**: Add timer and statistics tracking
3. **Mark for Review**: Allow flagging difficult cards
4. **Shuffle Mode**: Randomize card order
5. **Spaced Repetition**: Implement SRS algorithm
6. **User Notes**: Add note-taking functionality
7. **Export**: Export deck as PDF or other formats
8. **Analytics**: Track study patterns and effectiveness

## Resources

- **Angular Animations**: https://angular.dev/guide/animations
- **PrimeNG Components**: https://primeng.org/
- **PrimeNG Theming**: https://primeng.org/theming
- **Angular Signals**: https://angular.dev/guide/signals
- **WCAG Guidelines**: https://www.w3.org/WAI/WCAG21/quickref/

## Support

For questions or issues:
1. Check this guide first
2. Review the implementation report (FLASHCARD_VIEWER_IMPLEMENTATION.md)
3. Check Angular/PrimeNG documentation
4. Review CLAUDE.md for project guidelines

---

**Last Updated**: 2025-10-17
**Component Version**: 1.0.0
**Angular Version**: 20.x
**PrimeNG Version**: Latest
