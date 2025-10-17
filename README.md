# OpenDeck

An AI-first application that transforms your university course materials into intelligent flashcards to supercharge your studying.

![OpenDeck Logo](images/opendeck_line_cropped.png)

## Overview

OpenDeck automatically reads and analyzes documents from your university class folders and generates high-quality flashcards using artificial intelligence. Simply organize your course materials in subfolders by class, and let the AI extract key concepts, definitions, and important information to create effective study aids.

## Features

- **Automated Flashcard Generation**: AI analyzes your course documents (PDFs, Word docs, slides, notes) and creates targeted flashcards
- **Multi-Class Organization**: Organize materials by class in subfolders for automatic categorization
- **Intelligent Content Extraction**: AI identifies the most important concepts, terms, and relationships from your materials
- **Study Optimization**: Generate flashcards that focus on the material most likely to appear on exams
- **Time-Saving**: Spend less time creating study materials and more time actually studying

## How It Works

1. Organize your course documents into subfolders by class (e.g., `Biology/`, `Calculus/`, `History/`)
2. Run OpenDeck to scan your folders
3. The AI processes each document, extracting key information
4. All information and response hace precise information on where the data is being read from so the user may corroborate. 
5. Review and study your automatically generated flashcards

## Getting Started

_(Setup instructions coming soon)_

## Tech stack
The web site using primeng and the latest version of angular. 
The site will be hosted on AWS.

## Future ideas
- Analy course content and generat new flashcards using AI lookup, adding the corresponding sources.
- Create dockerized onpremise server using python with best practices
- Host site on AWS using lambda, cloudfront and dynamoDB
- Connect to S3 for storage of different flash card groups and documents
- Add user configuration, settings, favorites and more
