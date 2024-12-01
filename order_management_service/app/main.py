from fastapi import FastAPI, WebSocket, HTTPException
from typing import List
from uuid import uuid4, UUID
from app.models import Order
from app.order_book import OrderBook
import asyncio
import json

app = FastAPI()
connections: List[WebSocket] = []

order_book = OrderBook()

# WebSocket endpoint for real-time communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    try:
        while True:
            # Keeping the WebSocket connection alive, awaiting any message
            await websocket.receive_text()
    except Exception as e:
        print(f"Websocket connection error: {e}")  # Log or handle as needed
        connections.remove(websocket)

# Function to broadcast trade information to all connected clients
async def broadcast_trade(trade_info: dict):
    for connection in connections:
        # Safeguarding against broken connections
        try:
            await connection.send_json(trade_info)
        except Exception as e:
            print(f"Error broadcasting trade: {e}")  # Log or handle as needed

# Function to send the order book snapshot to all connected clients
async def send_order_book_snapshot():
    while True:
        snapshot = {"bids": order_book.get_bids_snapshot(), "asks": order_book.get_asks_snapshot()}
        for connection in connections:
            try:
                await connection.send_json(snapshot)
            except Exception as e:
                connections.remove(connection)
        await asyncio.sleep(1)  # Adjust timing as needed

# Endpoint to place a new order
@app.post("/order/", response_model=Order)
async def place_order(order: Order):
    order.id = uuid4()  # Ensure every order has a unique ID
    await order_book.add_order(order)  # Add and try to match the order
    # Broadcast trade info if there are any trades after matching
    if order_book.trades:
        last_trade = order_book.trades[-1]
        await broadcast_trade(last_trade)
    return order

# Endpoint to modify an existing order
@app.put("/order/{order_id}", response_model=dict)
async def modify_order(order_id: str, updated_order: Order):
    updated_order.id = (order_id)  # Ensure ID matches the path parameter
    result = await order_book.modify_order(
        order_id, updated_order.quantity, updated_order.price
    )
    if result:
        return {"success": True, "message": "Order modified"}
    else:
        raise HTTPException(status_code=404, detail="Order not found or unable to modify")

# Endpoint to cancel an existing order
@app.delete("/order/{order_id}", response_model=dict)
async def cancel_order(order_id: str):
    result = await order_book.cancel_order((order_id))  # Implement cancel_order in OrderBook
    if result:
        return {"success": True, "message": "Order cancelled"}
    else:
        raise HTTPException(status_code=404, detail="Order not found")
    
# Endpoint to fetch details of a specific order
@app.get("/order/{order_id}", response_model=dict)
async def fetch_order(order_id: str):
    order = order_book.get_order(UUID(order_id))
    if order:
        # No need to calculate average traded price and traded quantity here
        order_info = {
            "order_id" : order_id,
            "order_price": order.price,
            "order_quantity": order.quantity,
            "average_traded_price": order_book.traded_price_cache[str(order_id)],
            "traded_quantity": order_book.traded_quantity_cache[str(order_id)],
            "order_alive": order.status == 'open'
        }
        return order_info
    else:
        raise HTTPException(status_code=404, detail="Order not found")

# Endpoint to get information about all orders
@app.get("/orders")
async def get_all_orders():
    # Combine buy and sell orders
    buy_orders_info = [{"id": order.id,
                        "quantity": order.quantity,
                        "price": order.price,
                        "side": order.side,
                        "status": order.status,
                        "filled_quantity": order.filled_quantity,
                        "average_traded_price": order_book.traded_price_cache[str(order.id)],
                        "traded_quantity": order_book.traded_quantity_cache[str(order.id)],
                        "order_alive": order.status == 'open'
                        } for order in order_book.buy_orders]
    
    sell_orders_info = [{"id": order.id,
                         "quantity": order.quantity,
                         "price": order.price,
                         "side": order.side,
                         "status": order.status,
                         "filled_quantity": order.filled_quantity,
                         "average_traded_price": order_book.traded_price_cache[str(order.id)],
                         "traded_quantity": order_book.traded_quantity_cache[str(order.id)],
                         "order_alive": order.status == 'open'
                         } for order in order_book.sell_orders]
    
    return {"buy_orders": buy_orders_info, "sell_orders": sell_orders_info}

# Function to save the order book state periodically
async def save_state_periodically(interval_seconds=1):
    while True:
        await asyncio.sleep(interval_seconds)
        state = order_book.get_state()
        with open('order_book_state.json', 'w') as file:
            json.dump(state, file)

# Endpoint to get information about all trades
@app.get("/trades")
async def get_all_trades():
    return order_book.trades

# Startup event to load the order book state from file (if available)
@app.on_event("startup")
async def startup_event():
    try:
        # Attempt to load the saved state
        with open('order_book_state.json', 'r') as file:
            state = json.load(file)
            order_book.load_state(state)
        print("Order book state loaded successfully.")
    except FileNotFoundError:
        # If no saved state file exists, start with a clean state
        print("No saved state found, starting with an empty order book.")
    except Exception as e:
        # Handle any other exceptions that might occur
        print(f"Failed to load saved state: {e}")
        
    asyncio.create_task(send_order_book_snapshot())
    asyncio.create_task(save_state_periodically(10))  # Adjust interval_seconds as needed
	
