"""
Import vocabulary words from CSV file
CSV Format: #,Reč,Značenje,Primer u rečenici
"""
import os
import sys
import django
import csv

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.reading.models import VocabularyWord
from django.contrib.auth import get_user_model

User = get_user_model()

# Get user (change email if needed)
user_email = 'branislav.teofilovic@gmail.com'
try:
    user = User.objects.get(email=user_email)
except User.DoesNotExist:
    print(f"User {user_email} not found!")
    sys.exit(1)

# Path to CSV
csv_path = 'frontend/lumina-library/goodreads/reci.csv'

print(f"=== IMPORTING VOCABULARY FROM {csv_path} ===\n")

imported_count = 0
skipped_count = 0

with open(csv_path, 'r', encoding='utf-8-sig') as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        try:
            word_text = row['Reč'].strip()
            definition = row['Značenje'].strip()
            context = row['Primer u rečenici'].strip()

            if not word_text or not definition:
                skipped_count += 1
                continue

            # Check if word already exists for this user
            existing = VocabularyWord.objects.filter(
                user=user,
                word=word_text
            ).exists()

            if existing:
                print(f"  Skipping '{word_text}' (already exists)")
                skipped_count += 1
                continue

            # Create vocabulary word
            VocabularyWord.objects.create(
                user=user,
                word=word_text,
                definition=definition,
                context=context,
                mastery='new',
                is_public=False
            )

            word_safe = word_text.encode('ascii', 'ignore').decode('ascii') or word_text[:20]
            print(f"  [OK] Imported: {word_safe}")
            imported_count += 1

        except Exception as e:
            print(f"  [ERROR] Error on row {reader.line_num}: {e}")
            skipped_count += 1

print(f"\n=== IMPORT COMPLETE ===")
print(f"Imported: {imported_count}")
print(f"Skipped: {skipped_count}")
