import { Component, HostListener, OnInit, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { trigger, transition, style, animate } from '@angular/animations';

// PrimeNG Imports
import { Card } from 'primeng/card';
import { Button } from 'primeng/button';
import { ProgressBar } from 'primeng/progressbar';
import { Tag } from 'primeng/tag';

// Models
import { FlashCardData, CardDirection } from './models/flashcard-data.interface';

@Component({
    selector: 'app-flashcard-viewer',
    imports: [
        CommonModule,
        Card,
        Button,
        ProgressBar,
        Tag
    ],
    templateUrl: './flashcard-viewer.component.html',
    styleUrls: ['./flashcard-viewer.component.scss'],
    animations: [
        trigger('cardSlide', [
            transition(':increment', [
                style({ transform: 'translateX(100%)', opacity: 0 }),
                animate('300ms ease-out', style({ transform: 'translateX(0)', opacity: 1 }))
            ]),
            transition(':decrement', [
                style({ transform: 'translateX(-100%)', opacity: 0 }),
                animate('300ms ease-out', style({ transform: 'translateX(0)', opacity: 1 }))
            ])
        ]),
        trigger('fadeIn', [
            transition(':enter', [
                style({ opacity: 0, transform: 'translateY(10px)' }),
                animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
            ])
        ])
    ]
})
export class FlashcardViewerComponent implements OnInit {
    // Reactive state using signals
    deckTitle = signal<string>('');
    cards = signal<FlashCardData[]>([]);
    currentIndex = signal<number>(0);
    showAnswer = signal<boolean>(false);
    animationTrigger = signal<number>(0);

    // Computed values
    currentCard = computed(() => this.cards()[this.currentIndex()]);
    progress = computed(() => {
        const total = this.cards().length;
        return total > 0 ? ((this.currentIndex() + 1) / total) * 100 : 0;
    });
    isFirstCard = computed(() => this.currentIndex() === 0);
    isLastCard = computed(() => this.currentIndex() === this.cards().length - 1);
    cardCountText = computed(() => {
        const current = this.currentIndex() + 1;
        const total = this.cards().length;
        return `Card ${current} of ${total}`;
    });

    constructor(
        private route: ActivatedRoute,
        private router: Router
    ) {}

    ngOnInit(): void {
        // Get deck ID from route parameters
        const deckId = this.route.snapshot.paramMap.get('deckId');

        if (deckId) {
            this.loadDeckData(parseInt(deckId, 10));
        } else {
            // No deck ID provided, navigate back to listing
            this.router.navigate(['/pages/flashcards']);
        }
    }

    /**
     * Load deck data based on deck ID
     * In a real application, this would fetch from a service/API
     */
    private loadDeckData(deckId: number): void {
        // Mock data based on deck IDs from the listing component
        const mockDecks = this.getMockDeckData();
        const deck = mockDecks.find(d => d.id === deckId);

        if (deck) {
            this.deckTitle.set(deck.title);
            this.cards.set(deck.cards);
        } else {
            // Deck not found, navigate back
            this.router.navigate(['/pages/flashcards']);
        }
    }

    /**
     * Mock deck data with flashcards
     * This matches the decks from flashcard-decks-list.component.ts
     */
    private getMockDeckData() {
        return [
            {
                id: 1,
                title: 'Introduction to Computer Science',
                cards: [
                    {
                        id: 1,
                        question: 'What is an algorithm?',
                        answer: 'An algorithm is a step-by-step procedure or set of rules designed to solve a specific problem or perform a computation. It takes input, processes it through a finite sequence of well-defined instructions, and produces output.',
                        source: 'Introduction_to_CS_Lecture_01.pdf - Page 12, Section 2.1',
                        sourceUrl: '#'
                    },
                    {
                        id: 2,
                        question: 'What is the difference between a compiler and an interpreter?',
                        answer: 'A compiler translates the entire source code into machine code before execution, creating an executable file. An interpreter translates and executes code line-by-line at runtime. Compilers generally produce faster-running programs, while interpreters offer better debugging capabilities.',
                        source: 'Programming_Fundamentals.pdf - Page 45-46, Section 4.3',
                        sourceUrl: '#'
                    },
                    {
                        id: 3,
                        question: 'What is Big O notation used for?',
                        answer: 'Big O notation is used to describe the upper bound of an algorithm\'s time or space complexity, representing the worst-case scenario. It helps programmers analyze and compare the efficiency of different algorithms as input size grows.',
                        source: 'Algorithm_Analysis.pdf - Page 78, Section 6.2'
                    },
                    {
                        id: 4,
                        question: 'Define encapsulation in object-oriented programming.',
                        answer: 'Encapsulation is the bundling of data (attributes) and methods that operate on that data within a single unit (class), while restricting direct access to some components. This is achieved through access modifiers (private, public, protected) and promotes data hiding and modularity.',
                        source: 'OOP_Principles_Lecture_05.pdf - Page 23-24, Section 3.1',
                        sourceUrl: '#'
                    },
                    {
                        id: 5,
                        question: 'What is a stack data structure and what are its primary operations?',
                        answer: 'A stack is a linear data structure that follows the Last-In-First-Out (LIFO) principle. Its primary operations are: push (add element to top), pop (remove element from top), peek (view top element without removing), and isEmpty (check if stack is empty).',
                        source: 'Data_Structures_Chapter_03.pdf - Page 56-58'
                    }
                ]
            },
            {
                id: 2,
                title: 'Organic Chemistry Basics',
                cards: [
                    {
                        id: 1,
                        question: 'What are functional groups in organic chemistry?',
                        answer: 'Functional groups are specific groups of atoms within molecules that are responsible for the characteristic chemical reactions of those molecules. Common examples include hydroxyl (-OH), carbonyl (C=O), carboxyl (-COOH), and amino (-NH2) groups.',
                        source: 'Organic_Chemistry_Chapter_02.pdf - Page 34, Section 2.3',
                        sourceUrl: '#'
                    },
                    {
                        id: 2,
                        question: 'Explain the concept of chirality.',
                        answer: 'Chirality refers to a molecule that is non-superimposable on its mirror image, much like left and right hands. A chiral molecule contains a carbon atom bonded to four different groups, called a stereocenter or chiral center. Enantiomers are pairs of chiral molecules that are mirror images.',
                        source: 'Stereochemistry_Lecture_Notes.pdf - Page 12-15, Section 1.4'
                    },
                    {
                        id: 3,
                        question: 'What is an alkene and how does it differ from an alkane?',
                        answer: 'An alkene is a hydrocarbon containing at least one carbon-carbon double bond (C=C), with the general formula CnH2n. An alkane contains only single bonds (C-C) with formula CnH2n+2. Alkenes are more reactive than alkanes due to the presence of the pi bond.',
                        source: 'Hydrocarbons_Chapter_04.pdf - Page 67-68',
                        sourceUrl: '#'
                    }
                ]
            },
            {
                id: 3,
                title: 'Calculus I: Derivatives',
                cards: [
                    {
                        id: 1,
                        question: 'What is the formal definition of a derivative?',
                        answer: 'The derivative of a function f(x) at a point x is defined as the limit: f\'(x) = lim(h→0) [f(x+h) - f(x)]/h, representing the instantaneous rate of change of the function at that point.',
                        source: 'Calculus_Textbook_Chapter_03.pdf - Page 89, Definition 3.1',
                        sourceUrl: '#'
                    },
                    {
                        id: 2,
                        question: 'State the Chain Rule for derivatives.',
                        answer: 'The Chain Rule states that if y = f(g(x)), then dy/dx = f\'(g(x)) × g\'(x). In other words, the derivative of a composite function is the derivative of the outer function evaluated at the inner function, multiplied by the derivative of the inner function.',
                        source: 'Differentiation_Rules.pdf - Page 45, Theorem 4.2'
                    }
                ]
            },
            {
                id: 4,
                title: 'World History: Ancient Civilizations',
                cards: [
                    {
                        id: 1,
                        question: 'What were the key features of Mesopotamian civilization?',
                        answer: 'Mesopotamian civilization, located between the Tigris and Euphrates rivers, featured: the development of cuneiform writing, ziggurats (temple structures), sophisticated irrigation systems, the Code of Hammurabi (one of the earliest law codes), and advances in mathematics and astronomy.',
                        source: 'Ancient_Civilizations_Chapter_02.pdf - Page 34-38, Section 2.2',
                        sourceUrl: '#'
                    },
                    {
                        id: 2,
                        question: 'Describe the significance of the Roman Republic\'s government structure.',
                        answer: 'The Roman Republic (509-27 BCE) established a system of checks and balances with: two consuls elected annually, the Senate (advisory body of aristocrats), popular assemblies, and the position of tribune to protect plebeian rights. This influenced modern democratic systems.',
                        source: 'Roman_History_Lecture_08.pdf - Page 23-26'
                    }
                ]
            },
            {
                id: 5,
                title: 'Microeconomics Principles',
                cards: [
                    {
                        id: 1,
                        question: 'What is the Law of Demand?',
                        answer: 'The Law of Demand states that, all else being equal (ceteris paribus), as the price of a good or service increases, the quantity demanded decreases, and vice versa. This creates a downward-sloping demand curve.',
                        source: 'Microeconomics_Principles_Chapter_04.pdf - Page 56, Section 4.1',
                        sourceUrl: '#'
                    },
                    {
                        id: 2,
                        question: 'Define consumer surplus.',
                        answer: 'Consumer surplus is the difference between the maximum price a consumer is willing to pay for a good or service and the actual price paid. It represents the benefit consumers receive from purchasing at market price and is shown graphically as the area below the demand curve and above the market price.',
                        source: 'Market_Analysis_Textbook.pdf - Page 112-114, Section 7.3'
                    }
                ]
            },
            {
                id: 6,
                title: 'Data Structures & Algorithms',
                cards: [
                    {
                        id: 1,
                        question: 'Explain the difference between BFS and DFS graph traversal.',
                        answer: 'BFS (Breadth-First Search) explores all neighbors at the current depth before moving to nodes at the next depth level, using a queue. DFS (Depth-First Search) explores as far as possible along each branch before backtracking, using a stack or recursion. BFS finds shortest paths in unweighted graphs; DFS uses less memory for deep graphs.',
                        source: 'Graph_Algorithms_Chapter_09.pdf - Page 145-148, Section 9.2',
                        sourceUrl: '#'
                    },
                    {
                        id: 2,
                        question: 'What is the time complexity of QuickSort?',
                        answer: 'QuickSort has an average-case time complexity of O(n log n) and worst-case complexity of O(n²). The worst case occurs when the pivot consistently divides the array into highly unbalanced partitions (e.g., already sorted array with poor pivot selection). Space complexity is O(log n) due to recursion stack.',
                        source: 'Sorting_Algorithms_Analysis.pdf - Page 78-82, Section 5.4'
                    }
                ]
            }
        ];
    }

    /**
     * Navigate to the next flashcard
     */
    nextCard(): void {
        if (!this.isLastCard()) {
            this.currentIndex.update(i => i + 1);
            this.showAnswer.set(false);
            this.animationTrigger.update(v => v + 1);
        }
    }

    /**
     * Navigate to the previous flashcard
     */
    previousCard(): void {
        if (!this.isFirstCard()) {
            this.currentIndex.update(i => i - 1);
            this.showAnswer.set(false);
            this.animationTrigger.update(v => v - 1);
        }
    }

    /**
     * Toggle answer visibility
     */
    toggleAnswer(): void {
        this.showAnswer.update(v => !v);
    }

    /**
     * Navigate back to the deck listing
     */
    backToDecks(): void {
        this.router.navigate(['/pages/flashcards']);
    }

    /**
     * Keyboard navigation support
     * - Arrow Left: Previous card
     * - Arrow Right: Next card
     * - Space/Enter: Toggle answer
     */
    @HostListener('document:keydown', ['$event'])
    handleKeyboardEvent(event: KeyboardEvent): void {
        switch (event.key) {
            case 'ArrowLeft':
                event.preventDefault();
                this.previousCard();
                break;
            case 'ArrowRight':
                event.preventDefault();
                this.nextCard();
                break;
            case ' ':
            case 'Enter':
                event.preventDefault();
                this.toggleAnswer();
                break;
            case 'Escape':
                event.preventDefault();
                this.backToDecks();
                break;
        }
    }

    /**
     * Open source URL in new tab
     */
    openSource(url: string): void {
        if (url && url !== '#') {
            window.open(url, '_blank', 'noopener,noreferrer');
        }
    }
}
