from sqlalchemy import create_engine, String, Integer, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from app.config import DATABASE_URL
from pathlib import Path

if DATABASE_URL.startswith("sqlite"):
    Path("data").mkdir(exist_ok=True)
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), default="")
    full_name: Mapped[str] = mapped_column(String(200), default="")
    points: Mapped[int] = mapped_column(Integer, default=0)
    referred_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())

class Referral(Base):
    __tablename__ = "referrals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    referrer_id: Mapped[int] = mapped_column(Integer, index=True)
    referred_user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    rewarded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())

class PointTransaction(Base):
    __tablename__ = "point_transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, index=True)
    amount: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(250))
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())

class ForceChannel(Base):
    __tablename__ = "force_channels"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    invite_link: Mapped[str] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str] = mapped_column(String(250), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

class KeyItem(Base):
    __tablename__ = "key_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    package_name: Mapped[str] = mapped_column(String(50), index=True)
    key_value: Mapped[str] = mapped_column(Text, unique=True)
    sold: Mapped[bool] = mapped_column(Boolean, default=False)
    sold_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    added_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, index=True)
    product_name: Mapped[str] = mapped_column(String(120), default="")
    package_name: Mapped[str] = mapped_column(String(50))
    points_spent: Mapped[int] = mapped_column(Integer)
    key_value: Mapped[str] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())

class RedeemCode(Base):
    __tablename__ = "redeem_codes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    points: Mapped[int] = mapped_column(Integer)
    max_uses: Mapped[int] = mapped_column(Integer, default=1)
    uses: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class RedeemUse(Base):
    __tablename__ = "redeem_uses"
    __table_args__ = (UniqueConstraint("code_id", "telegram_id", name="uq_redeem_user"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code_id: Mapped[int] = mapped_column(ForeignKey("redeem_codes.id"))
    telegram_id: Mapped[int] = mapped_column(Integer)

def init_db():
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        if session.query(Product).count() == 0:
            for index in range(1, 6):
                session.add(Product(name=f"Panel {index}", description="Edit this product name in Admin Panel", sort_order=index))
            session.commit()

def get_session():
    return SessionLocal()
