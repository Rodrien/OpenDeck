#!/usr/bin/env python3
"""
Load test flashcard data from JSON files into the database.

This script loads flashcard data from the cards/ directory structure
into the database for local testing purposes.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import uuid

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.models import UserModel, DeckModel, CardModel, TopicModel, deck_topics, card_topics
from app.db.base import SessionLocal, engine, Base


def load_flashcards_from_json(json_path: Path, user_id: str, db: Session):
    """Load flashcards from a JSON file into the database."""

    print(f"\n📖 Loading flashcards from: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    course_name = data.get('course', json_path.parent.name)
    sources = data.get('sources', [])
    topics_data = data.get('topics', [])

    print(f"   Course: {course_name}")
    print(f"   Total cards: {data.get('totalCards', 0)}")
    print(f"   Topics: {len(topics_data)}")

    # Create the deck
    deck = DeckModel(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=course_name,
        description=f"Flashcards for {course_name}. Sources: {', '.join(sources)}",
        category="Academic",
        difficulty="INTERMEDIATE",
        card_count=data.get('totalCards', 0),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(deck)
    db.flush()  # Get the deck ID

    print(f"   ✅ Created deck: {deck.title} (ID: {deck.id})")

    # Track topics and cards
    topic_map = {}  # topic_name -> TopicModel
    cards_created = 0

    # Process each topic and its cards
    for topic_data in topics_data:
        topic_name = topic_data.get('name', 'Untitled Topic')
        cards_data = topic_data.get('cards', [])

        # Check if topic already exists
        existing_topic = db.query(TopicModel).filter(TopicModel.name == topic_name).first()

        if existing_topic:
            topic = existing_topic
            print(f"   📌 Using existing topic: {topic_name}")
        else:
            # Create new topic
            topic = TopicModel(
                id=str(uuid.uuid4()),
                name=topic_name,
                description=f"Topic from {course_name}",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(topic)
            db.flush()
            print(f"   ✨ Created topic: {topic_name} (ID: {topic.id})")

        topic_map[topic_name] = topic

        # Associate topic with deck
        db.execute(
            deck_topics.insert().values(
                deck_id=deck.id,
                topic_id=topic.id
            )
        )

        # Create cards for this topic
        for card_data in cards_data:
            card = CardModel(
                id=str(uuid.uuid4()),
                deck_id=deck.id,
                question=card_data.get('question', ''),
                answer=card_data.get('answer', ''),
                source=card_data.get('source', ''),
                source_url=None,  # Not provided in the JSON
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(card)
            db.flush()

            # Associate card with topic
            db.execute(
                card_topics.insert().values(
                    card_id=card.id,
                    topic_id=topic.id
                )
            )

            cards_created += 1

        print(f"      └─ Added {len(cards_data)} cards to topic '{topic_name}'")

    db.commit()
    print(f"   ✅ Successfully loaded {cards_created} cards into deck '{course_name}'")

    return deck


def create_test_user(db: Session) -> UserModel:
    """Create or get the test user."""

    test_email = "test@opendeck.com"

    # Check if user already exists
    existing_user = db.query(UserModel).filter(UserModel.email == test_email).first()

    if existing_user:
        print(f"👤 Using existing test user: {test_email}")
        return existing_user

    # Create new test user with properly hashed password
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    user = UserModel(
        id=str(uuid.uuid4()),
        email=test_email,
        name="Test User",
        password_hash=pwd_context.hash("password123"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()

    print(f"✨ Created test user: {test_email}")
    print(f"   Password: password123")
    print(f"   User ID: {user.id}")

    return user


def main():
    """Main function to load all test data."""

    print("=" * 70)
    print("🚀 OpenDeck Test Data Loader")
    print("=" * 70)

    # Create database session
    db = SessionLocal()

    try:
        # Create or get test user
        user = create_test_user(db)

        # Find all flashcard JSON files
        # First try relative to script location (when run from host)
        cards_dir = Path(__file__).parent.parent.parent / "cards"

        # If not found, try from container mount point
        if not cards_dir.exists():
            cards_dir = Path("/app/cards")

        if not cards_dir.exists():
            print(f"❌ Cards directory not found. Tried:")
            print(f"   - {Path(__file__).parent.parent.parent / 'cards'}")
            print(f"   - /app/cards")
            return

        json_files = list(cards_dir.glob("**/flashcards.json"))

        if not json_files:
            print(f"❌ No flashcards.json files found in {cards_dir}")
            return

        print(f"\n📂 Found {len(json_files)} flashcard file(s)")

        # Load each flashcard file
        decks_created = []
        for json_path in json_files:
            try:
                deck = load_flashcards_from_json(json_path, user.id, db)
                decks_created.append(deck)
            except Exception as e:
                print(f"   ❌ Error loading {json_path}: {e}")
                db.rollback()
                continue

        print("\n" + "=" * 70)
        print("✅ Data loading complete!")
        print("=" * 70)
        print(f"   Decks created: {len(decks_created)}")
        print(f"   User: {user.email} (password: password123)")
        print("\n💡 You can now login to the application with these credentials")
        print("   and explore the loaded flashcards!")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
