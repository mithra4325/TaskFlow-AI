"""Management command to safely verify MongoDB connectivity and read/write persistence.

Safe: Never prints or exposes credentials or connection strings.
Isolated: Writes a temporary test record, verifies reading it, and cleans it up.
"""

from datetime import datetime, timezone
import os
from django.core.management.base import BaseCommand
from myapp.mongo_service import check_mongo_connection, get_mongo_db


class Command(BaseCommand):
    help = "Safely verify MongoDB connection and test read/write without exposing secrets."

    def handle(self, *args, **options):
        self.stdout.write("Testing MongoDB configuration...")

        diag = check_mongo_connection()
        if not diag.get('configured'):
            self.stdout.write(self.style.WARNING("MongoDB Status: UNCONFIGURED (MONGODB_URI is not set in environment)."))
            self.stdout.write("To configure: Add MONGODB_URI=your_connection_string to .env and re-run this command.")
            return

        if diag.get('status') != 'connected':
            self.stdout.write(self.style.ERROR(f"MongoDB Status: UNAVAILABLE ({diag.get('message')})"))
            return

        # Perform isolated read/write test
        db, err = get_mongo_db()
        if db is None:
            self.stdout.write(self.style.ERROR(f"Could not select database: {err}"))
            return

        try:
            coll = db['__test_verification__']
            test_doc = {
                'verification_test': True,
                'created_at': datetime.now(timezone.utc),
            }
            insert_result = coll.insert_one(test_doc)
            test_id = insert_result.inserted_id

            # Verify read
            found = coll.find_one({'_id': test_id})
            if not found:
                self.stdout.write(self.style.ERROR("MongoDB verification failed: Document inserted but could not be read back."))
                return

            # Clean up
            coll.delete_one({'_id': test_id})

            self.stdout.write(self.style.SUCCESS("MongoDB Connection: VERIFIED"))
            self.stdout.write(self.style.SUCCESS("Write & Read Persistence: CONFIRMED"))
            self.stdout.write(self.style.SUCCESS("Test record safely cleaned up."))

        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"MongoDB test transaction failed: {type(exc).__name__}"))
