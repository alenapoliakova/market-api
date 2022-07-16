import asyncpg
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker

from analyzer.db.schema import Item, Price, Base

from settings import config

engine = create_async_engine(
    f"postgresql+asyncpg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.POSTGRES_HOST}:{config.POSTGRES_PORT}/{config.POSTGRES_DB}",
    echo=True
)


async def create_tables():
    """Функция для удаления и создания таблиц БД."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    """Yield db session."""
    async with async_session() as session:
        yield session
        await session.commit()


async def update_item(session: AsyncSession, id: UUID, name: str, type_item: str, parent_id: UUID = None):
    """Обновление товара / категории в БД.

    Parameters:
        session (AsyncSession):
            Сессия в БД.
        id (UUID):
            Уникальный идентификатор товара / категории.
        name (str):
            Название товара / категории.
        type_item (str):
            Тип: Товар или категория.
        parent_id (UUID):
            ID родителя товара / категории.

    Returns:
        result (sqlalchemy.engine.cursor.CursorResult):
            Добавленный элемент.
    """
    item_update = update(Item).values(
        {"name": name, "type": type_item, "parent_id": parent_id}
    ).where(Item.id == id).execution_options(synchronize_session="fetch")
    res = await session.execute(item_update)
    return res


async def add_item(session: AsyncSession, id, name: str, type_item: str, parent_id: UUID = None):
    """Добавление товара / категории в БД.

    Parameters:
        session (AsyncSession):
            Сессия в БД.
        id (UUID):
            Уникальный идентификатор товара / категории.
        name (str):
            Название товара / категории.
        type_item (str):
            Тип: Товар или категория.
        parent_id (UUID):
            ID родителя товара / категории.

    Returns:
        result (sqlalchemy.engine.cursor.CursorResult):
            Добавленный элемент.
    """
    item_row = await session.execute(select(Item).filter_by(id=id))
    if item_row.first():
        return await update_item(session, id, name, type_item, parent_id)
    else:
        if parent_id != "None":
            new_item = Item(id=id, name=name, type=type_item, parent_id=parent_id)
        else:
            new_item = Item(id=id, name=name, type=type_item)
        session.add(new_item)
        return new_item


async def add_price_for_item(session: AsyncSession, id: UUID, date: datetime, price: int):
    """Добавление даты и цены при обновлении товара в БД.

    Parameters:
        session (AsyncSession):
            Сессия в БД.
        id (UUID):
            Уникальный идентификатор товара.
        date (datetime):
            Время обновления цены товара.
        price (int):
            Стоимость товара.

    Returns:
        result (Price):
            Добавленный элемент.
    """
    new_price = Price(id=id, date=date, price=price)
    session.add(new_price)
    return new_price


async def delete_all_prices(session: AsyncSession, id: UUID):
    """Удаление всех цен для данного товара в БД.

    Parameters:
        session (AsyncSession):
            Сессия в БД.
        id (UUID):
            Уникальный идентификатор товара.

    Returns:
        None
    """
    item_row = await session.execute(select(Price).filter(Price.id == id))
    item_rows = item_row.scalars().fetchall()
    if item_rows:
        for item_row in item_rows:
            await session.delete(item_row)
            await session.commit()


async def delete_item(session: AsyncSession, id: UUID):
    """Удаление всей информации о товаре / категории.

    Parameters:
        session (AsyncSession):
            Сессия в БД.
        id (UUID):
            Уникальный идентификатор товара.

    Returns:
        item_row (Item):
            Удалённый элемент.
    """
    await delete_all_prices(session, id)
    item_row = await session.execute(select(Item).filter(Item.id == id))
    item_row = item_row.scalars().fetchall()
    if item_row:
        await session.delete(item_row[0])
        await session.commit()
        return item_row[0]
