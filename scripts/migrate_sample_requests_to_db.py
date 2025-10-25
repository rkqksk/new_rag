#!/usr/bin/env python3
"""
Migrate sample requests from JSON file to PostgreSQL database
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("Error: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


def get_db_connection():
    """Get PostgreSQL database connection"""
    # TODO: Load from environment variables or config
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'rag_enterprise'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres')
    )


def create_table(conn):
    """Create sample_requests table if not exists"""
    sql_file = project_root / 'scripts' / 'create_sample_requests_table.sql'

    with open(sql_file, 'r') as f:
        sql = f.read()

    with conn.cursor() as cur:
        # Note: We need to remove the FOREIGN KEY constraint for now
        # since we don't have a products table yet
        sql_no_fk = sql.replace(
            "CONSTRAINT fk_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE",
            "-- Foreign key will be added when products table is created"
        )
        cur.execute(sql_no_fk)
        conn.commit()
        print("✅ Table created successfully")


def migrate_json_to_db(conn):
    """Migrate data from JSON file to database"""
    json_file = project_root / 'data' / 'sample_requests.json'

    if not json_file.exists():
        print(f"⚠️  No JSON file found at {json_file}")
        return 0

    with open(json_file, 'r', encoding='utf-8') as f:
        requests = json.load(f)

    if not requests:
        print("⚠️  No sample requests to migrate")
        return 0

    migrated_count = 0
    skipped_count = 0

    with conn.cursor() as cur:
        for req in requests:
            try:
                # Check if already exists
                cur.execute(
                    "SELECT id FROM sample_requests WHERE id = %s",
                    (req['id'],)
                )
                if cur.fetchone():
                    print(f"⏭️  Skipping existing request: {req['id']}")
                    skipped_count += 1
                    continue

                # Insert new request
                cur.execute("""
                    INSERT INTO sample_requests (
                        id, product_id, product_name, product_code,
                        company_name, contact_name, contact_phone, contact_email,
                        request_qty, request_message,
                        status, created_at
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s,
                        %s, %s
                    )
                """, (
                    req['id'],
                    req['product_id'],
                    req['product_name'],
                    req['product_code'],
                    req['company_name'],
                    req['contact_name'],
                    req['contact_phone'],
                    req['contact_email'],
                    req.get('request_qty'),
                    req.get('request_message'),
                    req.get('status', 'pending'),
                    req.get('created_at', datetime.now())
                ))
                migrated_count += 1
                print(f"✅ Migrated request: {req['product_name']} - {req['company_name']}")

            except Exception as e:
                print(f"❌ Error migrating request {req.get('id', 'unknown')}: {e}")
                continue

        conn.commit()

    print(f"\n📊 Migration complete: {migrated_count} inserted, {skipped_count} skipped")
    return migrated_count


def verify_migration(conn):
    """Verify migration was successful"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Get total count
        cur.execute("SELECT COUNT(*) as total FROM sample_requests")
        result = cur.fetchone()
        print(f"\n📈 Total sample requests in DB: {result['total']}")

        # Get stats by status
        cur.execute("""
            SELECT status, COUNT(*) as count
            FROM sample_requests
            GROUP BY status
            ORDER BY count DESC
        """)
        print("\n📊 Requests by status:")
        for row in cur.fetchall():
            print(f"  - {row['status']}: {row['count']}")

        # Get top requested products
        cur.execute("""
            SELECT product_name, product_code, COUNT(*) as request_count
            FROM sample_requests
            GROUP BY product_name, product_code
            ORDER BY request_count DESC
            LIMIT 10
        """)
        results = cur.fetchall()
        if results:
            print("\n🔥 Top 10 requested products:")
            for row in results:
                print(f"  - {row['product_name']} ({row['product_code']}): {row['request_count']} requests")


def main():
    """Main migration function"""
    print("🚀 Starting sample requests migration to PostgreSQL...\n")

    try:
        # Connect to database
        conn = get_db_connection()
        print("✅ Connected to PostgreSQL\n")

        # Create table
        print("📋 Creating table...")
        create_table(conn)

        # Migrate data
        print("\n📦 Migrating data...")
        migrated_count = migrate_json_to_db(conn)

        if migrated_count > 0:
            # Verify migration
            verify_migration(conn)

        conn.close()
        print("\n✨ Migration completed successfully!")

    except psycopg2.OperationalError as e:
        print(f"❌ Database connection error: {e}")
        print("\n💡 Make sure PostgreSQL is running and credentials are correct.")
        print("   Set environment variables: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
