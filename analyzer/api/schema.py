from enum import Enum
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class ShopUnitType(str, Enum):
    offer = "OFFER"
    category = "CATEGORY"


class ShopUnitImport(BaseModel):
    id: UUID = Field(..., description="Уникальный идентификатор")
    name: str = Field(..., description="Имя элемента")
    parent_id: UUID | None = Field(default=None, description="UUID родительской категории", alias="parentId")
    type: ShopUnitType = Field(..., description="Тип элемента - категория или товар")
    price: Optional[int] = Field(default=None, description="Целое число, для категорий поле содержит None")

    class Config:
        schema_extra = {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66a444",
                "name": "Оффер",
                "parentId": "3fa85f64-5717-4562-b3fc-2c963f66a333",
                "type": "OFFER",
                "price": 234
            }
        }


class ShopUnitImportRequest(BaseModel):
    items: list[ShopUnitImport] = Field(..., description="Импортируемые элементы")
    update_date: datetime = Field(..., description="Время обновления добавляемых товаров/категорий",
                                  example="2022-05-28T21:12:01.516Z", alias="updateDate")


class ShopUnitStatisticUnit(ShopUnitImport):
    date: datetime = Field(..., description="Время последнего обновления элемента.", example="2022-05-28T21:12:01.516Z")

    class Config:
        schema_extra = {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66a444",
                "name": "Оффер", "date": "2022-05-28T21:12:01.516Z",
                "parentId": "3fa85f64-5717-4562-b3fc-2c963f66a333",
                "price": 234,
                "type": "OFFER"
            }
        }


class ShopUnitStatisticsResponse(BaseModel):
    items: ShopUnitStatisticUnit = Field(..., description="История в произвольном порядке")


class Error(BaseModel):
    code: int
    detail: str
