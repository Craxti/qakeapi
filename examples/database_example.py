"""
QakeAPI Database Connection Pooling Example

This example demonstrates how to use database connection pooling with QakeAPI.
"""
from qakeapi import QakeAPI, Request
from qakeapi.database.pool import ConnectionPool, DatabaseConfig

app = QakeAPI(
    title="Database Example",
    description="Example of database connection pooling in QakeAPI",
    version="1.0.0",
)

# Initialize database connection pool
# Note: This is a simplified example. In production, use environment variables for credentials.
db_pool = None


@app.on_event("startup")
async def startup():
    """Initialize database pool on startup"""
    global db_pool
    try:
        # Example: SQLite (no credentials needed)
        config = DatabaseConfig(
            url="sqlite:///./example.db",
            min_size=2,
            max_size=10,
        )
        db_pool = ConnectionPool(config)
        await db_pool.initialize()
        print("Database pool initialized")
    except Exception as e:
        print(f"Failed to initialize database pool: {e}")


@app.on_event("shutdown")
async def shutdown():
    """Close database pool on shutdown"""
    global db_pool
    if db_pool:
        await db_pool.close()
        print("Database pool closed")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Database Example API"}


@app.get("/users/")
async def get_users():
    """
    Get all users from database

    This endpoint uses connection pooling for efficient database access.
    """
    if not db_pool:
        from qakeapi.core.exceptions import HTTPException
        from qakeapi.utils.status import status

        raise HTTPException(status.SERVICE_UNAVAILABLE, "Database not available")

    async with db_pool.get_connection() as conn:
        # Example query (SQLite syntax)
        # In production, use proper ORM or query builder
        cursor = await conn.execute("SELECT * FROM users LIMIT 10")
        rows = await cursor.fetchall()

        return {
            "users": [{"id": row[0], "name": row[1], "email": row[2]} for row in rows]
        }


@app.post("/users/")
async def create_user(request: Request):
    """
    Create a new user in database

    This endpoint demonstrates transaction handling with connection pooling.
    """
    if not db_pool:
        from qakeapi.core.exceptions import HTTPException
        from qakeapi.utils.status import status

        raise HTTPException(status.SERVICE_UNAVAILABLE, "Database not available")

    data = await request.json()

    async with db_pool.transaction() as conn:
        # Example insert (SQLite syntax)
        # In production, use proper ORM or query builder
        cursor = await conn.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            (data.get("name"), data.get("email")),
        )
        user_id = cursor.lastrowid

        return {"id": user_id, **data}


@app.get("/db/stats")
async def db_stats():
    """Get database pool statistics"""
    if not db_pool:
        return {"status": "not_initialized"}

    stats = db_pool.get_stats()
    return {
        "status": "active",
        "pool_size": stats.get("pool_size", 0),
        "active_connections": stats.get("active_connections", 0),
        "idle_connections": stats.get("idle_connections", 0),
    }


if __name__ == "__main__":
    import uvicorn

    # Note: For this example to work, you need to create the database and table first
    # You can do this with a migration script or manually
    print("⚠️  Note: Make sure to create the database and 'users' table before running")

    uvicorn.run(app, host="0.0.0.0", port=8000)
