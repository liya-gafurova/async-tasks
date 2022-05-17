import asyncio
from typing import Any, Dict

import databases
import sqlalchemy

from sqlalchemy import DateTime, Column, String, Boolean, ForeignKey, sql

from communication_channels.utils import hash_password

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
    sqlalchemy.Column('username', String, unique=True),
    sqlalchemy.Column('password', String),
    sqlalchemy.Column('is_active', Boolean),
)

Rooms = sqlalchemy.Table(
    'rooms',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.String, primary_key=True),
    sqlalchemy.Column('name', sqlalchemy.String)

)

Messages = sqlalchemy.Table(
    'messages',
    metadata,
    Column("id", String, primary_key=True),
    Column("user_id", String, ForeignKey('users.id')),
    Column("room_id", String, ForeignKey('rooms.id')),

    Column("text", String),
    Column("created", DateTime(timezone=True), server_default=sql.func.now())
)
metadata.create_all(engine)


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


class CRUDUsers(CRUDBase):
    async def get_by_username(self, db, username: str):
        query = self.model.select().where(self.model.c.username == username)
        row = await db.fetch_one(query=query)
        return row

crud_users = CRUDUsers(Users)
crud_rooms = CRUDBase(Rooms)
crud_messages = CRUDBase(Messages)


async def test_rooms():
    id = '126'
    created = await crud_rooms.create(db=database, obj_in={'id': id, 'name': 'test_name'})

    updated = await crud_rooms.update(database, id, {"name": "new name"})

    gotten = await crud_rooms.get(database, id)

    gotten_all = await crud_rooms.get_all(database)

    deleted = await crud_rooms.delete(database, id)
    print(deleted)


async def test_users():
    id = '774'
    created = await crud_users.create(db=database, obj_in={'id': id,
                                                           'username': 'test user',
                                                           "is_active": True,
                                                           "password": hash_password("some password")})

    updated = await crud_users.update(database, id, {"username": "new name"})

    gotten = await crud_users.get(database, id)

    gotten2 = await crud_users.get_by_username(database, "new name")
    print(gotten2)

    gotten_all = await crud_users.get_all(database)
    print(gotten_all)

    # deleted = await crud_users.delete(database, id)
    # print(deleted)


async def test_messages():
    created_user = await crud_users.create(db=database, obj_in={'id': "4",
                                                           'username': 'test user',
                                                           "is_active": True,
                                                           "password": hash_password("some password")})

    created_room = await crud_rooms.create(db=database, obj_in={'id': "5", 'name': 'test_name'})

    id = '3'
    created = await crud_messages.create(db=database, obj_in={'id': id,
                                                           'user_id': "4",
                                                           "room_id": "5",
                                                           "text": "some message"})

    updated = await crud_messages.update(database, id, {"text": "new other message"})

    gotten = await crud_messages.get(database, id)

    gotten_all = await crud_messages.get_all(database)

    print(gotten_all)




async def test():
    # await test_rooms()
    await test_users()
    # await test_messages()

if __name__ == '__main__':
    asyncio.run(test())
