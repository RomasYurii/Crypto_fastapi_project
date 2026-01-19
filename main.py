from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from contextlib import asynccontextmanager
import httpx

from database import get_db, engine, Base
from models import CryptoPrice
import schemas



# 1. Lifespan (Ініціалізація БД при старті)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Створюємо таблиці, якщо їх немає
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("🚀 База даних готова!")
    yield
    print("🛑 Сервер зупинено")


app = FastAPI(title="Crypto Watcher", lifespan=lifespan)


# 2. Головний ендпоінт: Отримати ціну і зберегти
@app.get("/currency/{coin_id}", response_model=schemas.CryptoPriceRead)
async def get_coin_price(coin_id: str, db: AsyncSession = Depends(get_db)):
    """
    coin_id: наприклад 'bitcoin', 'ethereum', 'dogecoin'
    """

    # URL API CoinGecko
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"

    # --- БЛОК ЗАПИТУ В ІНТЕРНЕТ ---
    async with httpx.AsyncClient() as client:
        try:
            # Робимо GET запит (асинхронно!)
            response = await client.get(url)
            data = response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Помилка з'єднання з CoinGecko: {e}")

    # Перевіряємо, чи повернув CoinGecko дані (якщо ввели абракадабру)
    if coin_id not in data:
        raise HTTPException(status_code=404, detail="Currency not found")

    current_price = data[coin_id]['usd']

    # --- БЛОК ЗБЕРЕЖЕННЯ В БД ---
    # Створюємо запис у базі
    new_price = CryptoPrice(symbol=coin_id, price_usd=current_price)
    db.add(new_price)
    await db.commit()
    await db.refresh(new_price)

    return new_price


# 3. Ендпоінт історії: Останні 5 запитів
@app.get("/history", response_model=list[schemas.CryptoPriceRead])
async def get_history(db: AsyncSession = Depends(get_db)):
    # SELECT * FROM crypto_prices ORDER BY fetched_at DESC LIMIT 5
    query = select(CryptoPrice).order_by(desc(CryptoPrice.fetched_at)).limit(5)
    result = await db.execute(query)
    return result.scalars().all()