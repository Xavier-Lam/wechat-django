from django.db.backends.sqlite3 import schema


schema.DatabaseSchemaEditor.__enter__ = \
    schema.BaseDatabaseSchemaEditor.__enter__
