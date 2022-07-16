from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Item(Base):
    __tablename__ = "Item"
    id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    name = Column(Text, nullable=False)
    parent_id = Column(UUID(as_uuid=True), nullable=True)
    type = Column(Text, nullable=False)

    __mapper_args__ = {"eager_defaults": True}


class Price(Base):
    __tablename__ = "Price"
    index = Column(Integer, primary_key=True, autoincrement=True)

    id = Column(UUID(as_uuid=True), ForeignKey("Item.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    price = Column(Integer, nullable=False)
    bs = relationship("Item", foreign_keys=[id])
    __mapper_args__ = {"eager_defaults": True}
