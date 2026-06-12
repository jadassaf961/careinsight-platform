# Backend

FastAPI + SQLAlchemy + Alembic. Owns business logic, auth, audit, and PDF / chat services.

```bash
pip install ".[dev]"
alembic upgrade head
python -m app.db.seed         # optional dev seed
uvicorn app.main:app --reload
pytest
```

See [../docs/api.md](../docs/api.md) for the endpoint reference and
[../docs/database.md](../docs/database.md) for the schema.
