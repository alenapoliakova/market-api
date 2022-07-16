from datetime import datetime
from types import NoneType
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from analyzer.core import MarketTree
from .descriptions import *
from .schema import ShopUnitImportRequest
from analyzer.db.main import add_item, add_price_for_item, delete_item, create_tables, engine, get_session

tree = MarketTree()

app = FastAPI(
    title="Market Open API",
    description="API для загрузки товаров в Маркет товаров",
    version="1.0.0"
)

app.add_event_handler("startup", create_tables)
app.add_event_handler("shutdown", engine.dispose)


@app.post("/imports",
          tags=["Базовые запросы"],
          summary=load_items["summary"],
          description=load_items["description"],
          responses=load_items["responses"])
async def load_items(
        request: ShopUnitImportRequest,
        session: AsyncSession = Depends(get_session)
):
    date = request.update_date
    for item in request.items:
        if item.type.value == "OFFER" and isinstance(item.price, NoneType):
            raise HTTPException(status_code=400, detail="Validation Failed")
        tree.add(item.dict() | {"date": date})
        await add_item(session, item.id, item.name, item.type.value, item.parent_id)
        if item.price:
            await add_price_for_item(session, item.id, date, item.price)

    return {"code": 200, "message": "The insertion or update was successful"}


@app.delete("/delete/{id}",
            tags=["Базовые запросы"],
            summary=delete_item_by_id["summary"],
            description=delete_item_by_id["description"],
            responses=delete_item_by_id["responses"])
async def delete_item_by_id(
        id: UUID = Query(description="Идентификатор категории / товара",
                         example="3fa85f64-5717-4562-b3fc-2c963f66a333"),
        session: AsyncSession = Depends(get_session)
):
    deleted = await delete_item(session, id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    if id in tree.nodes[id] and tree.nodes[id]["type"].value == "OFFER":
        tree.delete_price_by_id(id)
    deleted = tree.delete_node_by_id(id)
    if deleted:
        return {"code": 200, "message": "OK"}


@app.get("/nodes/{id}",
         tags=["Базовые запросы"],
         summary=get_nodes_by_id["summary"],
         description=get_nodes_by_id["description"],
         responses=get_nodes_by_id["responses"])
def get_nodes_by_id(
        id: UUID = Query(description="Идентификатор категории / товара", example="3fa85f64-5717-4562-b3fc-2c963f66a333")
):
    if id not in tree.nodes:
        raise HTTPException(status_code=404, detail="Item not found")
    nodes = tree.get_nodes(tree.nodes[id])
    return nodes


@app.get("/sales",
         tags=["Дополнительные запросы"],
         summary=get_sales["summary"],
         description=get_sales["description"],
         responses=get_sales["responses"])
def get_sales(date: datetime = Query(description="Дата и время запроса", example="2022-05-28T21:12:01.516Z")):
    sales = tree.get_sales(date)
    return sales


@app.get("/node/{id}/statistic",
         tags=["Дополнительные запросы"],
         summary=get_statistic_by_id["summary"],
         description=get_statistic_by_id["description"],
         responses=get_statistic_by_id["responses"])
def get_statistic_by_id(
        id: UUID = Query(description="UUID товара / категории, для которой будет отображаться статистика",
                         example="2022-05-28T21:12:01.516Z"),
        dateStart: datetime = Query(default=None,
                                    description="Дата и время начала интервала, для которого считается статистика",
                                    example="2022-05-28T21:12:01.516Z"),
        dateEnd: datetime = Query(default=None,
                                  description="Дата и время конца интервала, для которого считается статистика",
                                  example="2022-05-28T21:12:01.516Z")):
    if dateEnd and dateStart and dateEnd < dateStart:
        raise HTTPException(status_code=400, detail="Validation Failed")
    if id not in tree.nodes:
        raise HTTPException(status_code=404, detail="Item not found")
    statistic = tree.get_statistic_by_id(id, dateStart, dateEnd)
    return statistic
