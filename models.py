from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database import Base

class CryptoPrice(Base):
    __tablename__ = "crypto_prices"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)  # Наприклад: "bitcoin"
    price_usd = Column(Float)            # Наприклад: 95000.50
    fetched_at = Column(DateTime(timezone=True), server_default=func.now()) # Час запиту