from typing import Dict, Any

import databases
import sqlalchemy
from sqlalchemy import String, ForeignKey

DATABASE_URL = "sqlite:///./test.db"
database = databases.Database(DATABASE_URL)

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

metadata = sqlalchemy.MetaData()

Users = sqlalchemy.Table(
    'users',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.String, primary_key=True),
    sqlalchemy.Column('username', String, unique=True, nullable=False),
)

Tasks = sqlalchemy.Table(
    'tasks',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.String, primary_key=True),
    sqlalchemy.Column('user_id', String, ForeignKey('users.id')),
    sqlalchemy.Column('result', String, unique=True, nullable=False)
)


class CRUDBase:
    def __init__(self, model_type):
        self.model = model_type

    async def get(self, db, id: str):
        query = self.model.select().where(self.model.c.id == id)
        row = await db.fetch_one(query=query)
        return row

    async def get_all(self, db):
        query = self.model.select()
        rows = await db.fetch_all(query=query)
        return rows

    async def create(self, db, obj_in: Dict[str, Any]):
        query = self.model.insert().values(**obj_in)
        created = await db.execute(query=query)
        return created

    async def update(self, db, id: str, obj_in: Dict[str, Any]):
        query = self.model.update().where(self.model.c.id == id).values(**obj_in)
        updated = await db.execute(query=query)
        return updated

    async def delete(self, db, id: str):
        query = self.model.delete().where(self.model.c.id == id)
        deleted = await db.execute(query=query)
        return deleted


crud_tasks = CRUDBase(Tasks)
crud_users= CRUDBase(Users)