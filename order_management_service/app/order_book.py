from typing import List, Dict, Optional
from app.models import Order
from uuid import UUID, uuid4
from datetime import datetime
from typing import List, Dict, Optional, Union
import asyncio

class OrderBook:
    def __init__(self, broadcaster=None):
        # Initialize the order book with empty lists for buy and sell orders
        self.buy_orders: List[Order] = []
        self.sell_orders: List[Order] = []
        self.trades: List[Dict] = []  # List to store trade information
        self.broadcast_trade = broadcaster  # Function to broadcast trade information
        self.traded_price_cache: Dict[str, float] = {}  # Cache for average traded prices
        self.traded_quantity_cache: Dict[str, int] = {}  # Cache for traded quantities

    async def add_order(self, order: Order):
        # Add the order to the appropriate list based on its side (buy/sell)
        if order.side == 1:
            self.buy_orders.append(order)
            self.buy_orders.sort(key=lambda x: -x.price)  # Sort buy orders by price descending
        else:
            self.sell_orders.append(order)
            self.sell_orders.sort(key=lambda x: x.price)  # Sort sell orders by price ascending

        # Initialize average traded price and quantity to 0
        self.traded_price_cache[str(order.id)] = 0
        self.traded_quantity_cache[str(order.id)] = 0
        
        await self.match_orders()  # Try to match orders after adding a new one

    async def match_orders(self):
        # Match buy and sell orders as long as there are both types of orders and their prices match
        while self.buy_orders and self.sell_orders and self.buy_orders[0].price >= self.sell_orders[0].price:
            buy_order = self.buy_orders[0]  # Get the highest buy order
            sell_order = self.sell_orders[0]  # Get the lowest sell order
            trade_quantity = min(buy_order.quantity - buy_order.filled_quantity, sell_order.quantity - sell_order.filled_quantity)
            
            buy_order.filled_quantity += trade_quantity  # Update filled quantity for buy order
            sell_order.filled_quantity += trade_quantity  # Update filled quantity for sell order
            
            # Create a trade object with relevant information
            trade = {
                "unique_id": str(uuid4()),  # Generate a unique ID for each trade
                "execution_timestamp": datetime.now().isoformat(),  # Add execution timestamp
                "buy_order_id": str(buy_order.id),
                "sell_order_id": str(sell_order.id),
                "price": sell_order.price,
                "quantity": trade_quantity
            }
            self.trades.append(trade)  # Add trade to the list of trades

            # Calculate average traded price and quantity for both buy and sell orders
            self.update_average_traded_price(buy_order.id)
            self.update_average_traded_price(sell_order.id)
            self.update_traded_quantity(buy_order.id)
            self.update_traded_quantity(sell_order.id)

            if buy_order.quantity == buy_order.filled_quantity:
                buy_order.status = 'filled'  # Update buy order status to 'filled'
                self.buy_orders.pop(0)  # Remove fully filled buy order from the list
            else:
                buy_order.status = 'partially filled'  # Update buy order status to 'partially filled'

            if sell_order.quantity == sell_order.filled_quantity:
                sell_order.status = 'filled'  # Update sell order status to 'filled'
                self.sell_orders.pop(0)  # Remove fully filled sell order from the list
            else:
                sell_order.status = 'partially filled'  # Update sell order status to 'partially filled'

            # Direct call to broadcast the trade
            if self.broadcast_trade:
                await self.broadcast_trade(trade)

    async def cancel_order(self, order_id: str) -> bool:
        # Cancel the order with the given ID if it exists
        if not isinstance(order_id, UUID):
            try:
                # Convert to UUID only if order_id is not already a UUID object
                uuid_order_id = UUID(order_id)
            except ValueError:
                # Handle invalid UUID string
                return False
        else:
            # If order_id is already a UUID object, use it directly
            uuid_order_id = order_id

        for order_list in [self.buy_orders, self.sell_orders]:
            for order in order_list:
                if order.id == uuid_order_id:
                    order_list.remove(order)  # Remove the order from the list
                    return True
        return False

    async def modify_order(self, order_id: str, new_quantity: int, new_price: float) -> Optional[Order]:
        # Modify the order with the given ID if it exists
        if not isinstance(order_id, UUID):
            try:
                uuid_order_id = UUID(order_id)
            except ValueError:
                # If order_id is not a valid UUID string, return None or handle as needed
                return None
        else:
            uuid_order_id = order_id
        
        for order_list in [self.buy_orders, self.sell_orders]:
            for order in order_list:
                if order.id == uuid_order_id:
                    order.quantity = new_quantity
                    order.price = new_price
                    # Re-sort the orders in case the price change affects order book placement
                    self.buy_orders.sort(key=lambda x: -x.price)
                    self.sell_orders.sort(key=lambda x: x.price)
                    await self.match_orders()  # Match orders after modifying an order
                    return order
        
        # Return None if no order with the given ID was found
        return None
    
    def get_bids_snapshot(self):
        # Return a snapshot of the top 5 buy orders
        return [{"price": order.price, "quantity": order.quantity} for order in self.buy_orders[:5]]

    def get_asks_snapshot(self):
        # Return a snapshot of the top 5 sell orders
        return [{"price": order.price, "quantity": order.quantity} for order in self.sell_orders[:5]]

    def get_order(self, order_id: UUID) -> Optional[Order]:
        # Get the order with the given ID
        for order in self.buy_orders + self.sell_orders:
            if order.id == order_id:
                return order
        return None

    def update_average_traded_price(self, order_id: str):
        # Update the average traded price for the order with the given ID
        total_price = 0
        total_quantity = 0
        for trade in self.trades:
            if str(trade["buy_order_id"]) == str(order_id) or str(trade["sell_order_id"]) == str(order_id):
                total_price += trade["price"] * trade["quantity"]
                total_quantity += trade["quantity"]
        
        average_price = total_price / total_quantity if total_quantity != 0 else 0
        self.traded_price_cache[str(order_id)] = average_price

    def update_traded_quantity(self, order_id: str):
        # Update the traded quantity for the order with the given ID
        total_quantity = sum(trade["quantity"] for trade in self.trades if trade["buy_order_id"] == str(order_id) or trade["sell_order_id"] == str(order_id))
        
        # Update the cache with the string representation of order_id
        self.traded_quantity_cache[str(order_id)] = total_quantity        
        return total_quantity

    def get_state(self):
        # Serialize all relevant attributes, including calculated ones.
        buy_orders = [{
            **order.dict(),
            "id": str(order.id),
            "average_traded_price": self.traded_price_cache.get(str(order.id), 0),
            "traded_quantity": self.traded_quantity_cache.get(str(order.id), 0),
            "order_alive": order.status != 'filled'
        } for order in self.buy_orders]

        sell_orders = [{
            **order.dict(),
            "id": str(order.id),
            "average_traded_price": self.traded_price_cache.get(str(order.id), 0),
            "traded_quantity": self.traded_quantity_cache.get(str(order.id), 0),
            "order_alive": order.status != 'filled'
        } for order in self.sell_orders]

        trades = [{
            **trade,
            "buy_order_id": str(trade["buy_order_id"]),
            "sell_order_id": str(trade["sell_order_id"]),
            "unique_id": str(trade.get("unique_id", uuid4())),
        } for trade in self.trades]
        
        state = {
            "buy_orders": buy_orders,
            "sell_orders": sell_orders,
            "trades": trades,
        }
        return state

    def load_state(self, state):
        # Deserialize the state, ensuring to convert UUID strings back and handle all attributes.
        self.buy_orders = [
            Order(**{
                **order_data, 
                "id": UUID(order_data["id"]),
                "status": 'open' if order_data["order_alive"] else 'filled'
            }) for order_data in state['buy_orders']
        ]
        self.sell_orders = [
            Order(**{
                **order_data, 
                "id": UUID(order_data["id"]),
                "status": 'open' if order_data["order_alive"] else 'filled'
            }) for order_data in state['sell_orders']
        ]
        self.trades = [
            {
                **trade,
                "buy_order_id": UUID(trade["buy_order_id"]),
                "sell_order_id": UUID(trade["sell_order_id"]),
                "unique_id": UUID(trade.get("unique_id", str(uuid4()))),
            } for trade in state['trades']
        ]
        
        # After loading, populate the calculated caches.
        for order in self.buy_orders + self.sell_orders:
            self.update_average_traded_price(str(order.id))
            self.update_traded_quantity(str(order.id))
