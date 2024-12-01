from pydantic import BaseModel
from typing import Optional
from uuid import UUID, uuid4

class Order(BaseModel):
    id: UUID = uuid4()  # Automatically generate a new UUID for each instance
    quantity: int
    price: float
    side: Optional[int] = None  # 1 for buy, -1 for sell
    status: str = "open"  # Default to "open"
    filled_quantity: int = 0  # Default to 0
