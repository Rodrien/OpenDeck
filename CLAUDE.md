# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

ADD LOGO HERE

## Project Overview

OpenDeck is an AI-first web application that automatically generates flashcards from university course documents. The app reads documents organized in class-specific subfolders and uses AI to extract key concepts for studying.

## Tech Stack

- **Frontend**: Angular (latest version) with PrimeNG component library
- **Hosting**: AWS
- **Future Storage**: AWS S3 for flashcard groups and documents

## Core Architecture

### Document Processing Pipeline
The application follows this workflow:
1. Users organize course materials into subfolders by class (e.g., `Biology101/`, `Calculus/`)
2. The system scans and processes documents (PDFs, Word docs, slides, notes)
3. AI extracts key concepts, definitions, and relationships
4. Flashcards are generated with source attribution
5. Users review and study the generated flashcards

### Source Attribution Requirement
**Critical**: All AI-generated responses and flashcards MUST include precise references to the source material (document name, page/section) so users can verify and corroborate the information.

## Development Commands

When the Angular project is set up, typical commands will include:
- `ng serve` - Run development server
- `ng build` - Build the application
- `ng test` - Run unit tests
- `ng lint` - Lint the codebase
- `npm install` - Install dependencies

## Future Architecture Considerations

### AWS Integration
- S3 buckets for document storage and flashcard persistence
- User authentication and authorization
- User-specific data (settings, favorites, configurations)

### Document Processing
- Support for multiple document formats (PDF, DOCX, PPTX, TXT)
- Folder-based class organization and categorization
- Metadata extraction and indexing

### AI Integration
- Integration with AI services for content extraction
- Natural language processing for concept identification
- Question-answer pair generation from source material
