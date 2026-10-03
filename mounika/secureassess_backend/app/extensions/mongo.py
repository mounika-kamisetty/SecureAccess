"""
SecureAssess — MongoDB Extension.

Initialises the PyMongo client, exposes collection accessors,
tests the MongoDB connection, and creates required indexes.
"""

from pymongo import MongoClient, ASCENDING
from pymongo.errors import (
    PyMongoError,
    ServerSelectionTimeoutError,
)


class MongoDB:
    """Thin wrapper around PyMongo for the application factory pattern."""

    def __init__(self):
        self.client = None
        self.db = None

    def init_app(self, app):
        """Connect to MongoDB and create indexes."""

        mongo_uri = app.config.get("MONGO_URI")
        mongo_db_name = app.config.get("MONGO_DB_NAME")

        # ------------------------------------------------------------
        # Validate configuration
        # ------------------------------------------------------------

        if not mongo_uri:
            raise RuntimeError(
                "MONGO_URI is not configured. "
                "Check your .env file and app/config.py."
            )

        if not mongo_db_name:
            raise RuntimeError(
                "MONGO_DB_NAME is not configured. "
                "Check your .env file and app/config.py."
            )

        print("\n" + "=" * 60)
        print("Connecting to MongoDB...")
        print(f"Database: {mongo_db_name}")
        print("=" * 60)

        try:

            # --------------------------------------------------------
            # Create MongoDB client
            # --------------------------------------------------------

            self.client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=10000,
            )

            # --------------------------------------------------------
            # Select database
            # --------------------------------------------------------

            self.db = self.client[mongo_db_name]

            # --------------------------------------------------------
            # Test connection
            # --------------------------------------------------------

            self.client.admin.command("ping")

            print("MongoDB connection: SUCCESS")

            # --------------------------------------------------------
            # Create indexes
            # --------------------------------------------------------

            self._ensure_indexes()

            print("MongoDB indexes: SUCCESS")
            print("=" * 60)
            print()

        except ServerSelectionTimeoutError as error:

            print("\n" + "=" * 60)
            print("MONGODB CONNECTION ERROR")
            print("=" * 60)

            print(
                "\nMongoDB could not be reached."
            )

            print(
                "\nPossible causes:"
            )

            print(
                "1. MongoDB is not running."
            )

            print(
                "2. MONGO_URI in .env is incorrect."
            )

            print(
                "3. MongoDB is running on another port."
            )

            print(
                "4. MongoDB Atlas/network access is blocked."
            )

            print(
                "\nOriginal error:"
            )

            print(error)

            print("=" * 60)

            raise

        except PyMongoError as error:

            print("\n" + "=" * 60)
            print("MONGODB ERROR")
            print("=" * 60)

            print(
                "\nMongoDB operation failed."
            )

            print(
                "\nOriginal error:"
            )

            print(error)

            print("=" * 60)

            raise

        except Exception as error:

            print("\n" + "=" * 60)
            print("MONGODB INITIALIZATION ERROR")
            print("=" * 60)

            print(
                "\nUnexpected error:"
            )

            print(error)

            print("=" * 60)

            raise

    # ------------------------------------------------------------------
    # Collection accessors
    # ------------------------------------------------------------------

    @property
    def users(self):
        return self.db["users"]

    @property
    def exams(self):
        return self.db["exams"]

    @property
    def attempts(self):
        return self.db["attempts"]

    @property
    def events(self):
        return self.db["events"]

    @property
    def audit_logs(self):
        return self.db["audit_logs"]

    @property
    def refresh_tokens(self):
        return self.db["refresh_tokens"]

    @property
    def blocklist(self):
        return self.db["blocklist"]

    # ------------------------------------------------------------------
    # Index creation
    # ------------------------------------------------------------------

    def _ensure_indexes(self):
        """Create indexes idempotently."""

        print("\nCreating MongoDB indexes...")

        # ------------------------------------------------------------
        # Users
        # ------------------------------------------------------------

        print("Creating users.email index...")

        self.users.create_index(
            [("email", ASCENDING)],
            unique=True,
            name="users_email_unique"
        )

        # ------------------------------------------------------------
        # Attempts
        # ------------------------------------------------------------

        print("Creating attempts indexes...")

        self.attempts.create_index(
            [("user_id", ASCENDING)],
            name="attempts_user_id"
        )

        self.attempts.create_index(
            [("exam_id", ASCENDING)],
            name="attempts_exam_id"
        )

        self.attempts.create_index(
            [
                ("user_id", ASCENDING),
                ("exam_id", ASCENDING),
                ("status", ASCENDING)
            ],
            name="attempts_user_exam_status"
        )

        # ------------------------------------------------------------
        # Events
        # ------------------------------------------------------------

        print("Creating events indexes...")

        self.events.create_index(
            [("attempt_id", ASCENDING)],
            name="events_attempt_id"
        )

        self.events.create_index(
            [("user_id", ASCENDING)],
            name="events_user_id"
        )

        # ------------------------------------------------------------
        # Audit logs
        # ------------------------------------------------------------

        print("Creating audit log indexes...")

        self.audit_logs.create_index(
            [("user_id", ASCENDING)],
            name="audit_logs_user_id"
        )

        self.audit_logs.create_index(
            [("timestamp", ASCENDING)],
            name="audit_logs_timestamp"
        )

        self.audit_logs.create_index(
            [("action", ASCENDING)],
            name="audit_logs_action"
        )

        # ------------------------------------------------------------
        # Refresh tokens
        # ------------------------------------------------------------

        print("Creating refresh token indexes...")

        self.refresh_tokens.create_index(
            [("token", ASCENDING)],
            unique=True,
            name="refresh_tokens_token_unique"
        )

        self.refresh_tokens.create_index(
            [("user_id", ASCENDING)],
            name="refresh_tokens_user_id"
        )

        self.refresh_tokens.create_index(
            [("expires_at", ASCENDING)],
            name="refresh_tokens_expires_at"
        )

        # ------------------------------------------------------------
        # Blocklist
        # ------------------------------------------------------------

        print("Creating blocklist indexes...")

        self.blocklist.create_index(
            [("jti", ASCENDING)],
            unique=True,
            name="blocklist_jti_unique"
        )

        self.blocklist.create_index(
            [("created_at", ASCENDING)],
            name="blocklist_created_at"
        )

        print("All MongoDB indexes created successfully.")


# ----------------------------------------------------------------------
# Singleton instance
# ----------------------------------------------------------------------

mongo = MongoDB()
