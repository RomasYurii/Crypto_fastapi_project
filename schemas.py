from datetime import datetime
from pydantic import BaseModel, ConfigDict

class CryptoPriceCreate(BaseModel):
    symbol: str
    price_usd: float

class CryptoPriceRead(BaseModel):
    id: int
    symbol: str
    price_usd: float
    fetched_at: datetime
    model_config = ConfigDict(from_attributes=True)