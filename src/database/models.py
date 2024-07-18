from typing import List, Optional
from sqlalchemy import ForeignKey, BigInteger, DateTime, UniqueConstraint
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


# TODO: refactor db structure
class Base(DeclarativeBase):
    pass


class Config(Base):
    __tablename__ = "config"
    id: Mapped[int] = mapped_column(primary_key=True)
    apify_key: Mapped[Optional[str]] = mapped_column(String(100))
    main_chat_id: Mapped[int] = mapped_column(BigInteger)
    log_thread_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    last_discovering_date: Mapped[int] = mapped_column(DateTime(timezone=True))
    twitter_objects: Mapped[List["TwitterObject"]] = relationship(
        "TwitterObject", back_populates="config"
    )

    def __repr__(self) -> str:
        return str(self.main_chat_id)


class TwitterObject(Base):
    __tablename__ = "twitter_object"
    id: Mapped[int] = mapped_column(primary_key=True)
    thread_id: Mapped[int] = mapped_column(BigInteger)
    twitter_username: Mapped[str] = mapped_column(String(100))
    config_id: Mapped[int] = mapped_column(ForeignKey("config.id"))

    config: Mapped[Config] = relationship("Config", back_populates="twitter_objects")

    __table_args__ = (
        UniqueConstraint("thread_id", "twitter_username", name="thread_username"),
    )

    def __repr__(self) -> str:
        return self.twitter_username