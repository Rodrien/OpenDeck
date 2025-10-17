import { Routes } from '@angular/router';
import { Documentation } from './documentation/documentation';
import { Crud } from './crud/crud';
import { Empty } from './empty/empty';
import { FlashcardDecksListComponent } from './flashcards/flashcard-decks-list.component';
import { FlashcardViewerComponent } from './flashcards/flashcard-viewer.component';

export default [
    { path: 'documentation', component: Documentation },
    { path: 'crud', component: Crud },
    { path: 'empty', component: Empty },
    { path: 'flashcards', component: FlashcardDecksListComponent },
    { path: 'flashcards/viewer/:deckId', component: FlashcardViewerComponent },
    { path: '**', redirectTo: '/notfound' }
] as Routes;
