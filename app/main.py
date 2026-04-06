if __package__ in {None, ""}:
    from app.db.mongo_db import get_mongo_database_info
    from app.db.postgres_db import get_postgres_database_info
else:
    from app.db.mongo_db import get_mongo_database_info
    from app.db.postgres_db import get_postgres_database_info


try:
    mongo_database_info = get_mongo_database_info()
    print(mongo_database_info)
except Exception as exc:
    print(f"MongoDB connection failed: {exc}")

try:
    postgres_database_info = get_postgres_database_info()
    print(postgres_database_info)
except Exception as exc:
    print(f"PostgreSQL connection failed: {exc}")
