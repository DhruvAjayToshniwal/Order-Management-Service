# Order Management Service

This project is an order management service built using FastAPI. It provides a RESTful API for managing buy and sell orders, along with real-time communication capabilities using WebSockets.

## Features

- **Order Management**: Place, modify, and cancel buy and sell orders.
- **Real-Time Updates**: Receive real-time updates on trades and order book snapshots via WebSockets.
- **Order Book State**: Periodically saves the order book state to a file and loads it on startup.

## API Endpoints

- **WebSocket Endpoint**: `/ws`
  - Connect to receive real-time updates on trades and order book snapshots.

- **Place Order**: `POST /order/`
  - Place a new buy or sell order.
  - Request Body: `Order` object.

- **Modify Order**: `PUT /order/{order_id}`
  - Modify an existing order's quantity and price.
  - Path Parameter: `order_id` (UUID).

- **Cancel Order**: `DELETE /order/{order_id}`
  - Cancel an existing order.
  - Path Parameter: `order_id` (UUID).

- **Fetch Order**: `GET /order/{order_id}`
  - Fetch details of a specific order.
  - Path Parameter: `order_id` (UUID).

- **Get All Orders**: `GET /orders`
  - Retrieve information about all buy and sell orders.

- **Get All Trades**: `GET /trades`
  - Retrieve information about all trades.

## Setup Instructions

1. **Install Dependencies**: Ensure you have Python installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**: Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Access the API**: Open your browser and navigate to `http://localhost:8000/docs` to explore the API documentation.

## Order Model

The `Order` model is defined as follows:
- `id`: UUID (automatically generated)
- `quantity`: int
- `price`: float
- `side`: Optional[int] (1 for buy, -1 for sell)
- `status`: str (default "open")
- `filled_quantity`: int (default 0)

## Order Book Logic

The `OrderBook` class handles the core logic for managing orders, including:
- Adding and matching orders.
- Modifying and canceling orders.
- Broadcasting trade information.
- Managing order book state.

## Real-Time Communication

The service uses WebSockets to provide real-time updates on trades and order book snapshots. Connect to the `/ws` endpoint to receive updates.

## License

This project is licensed under the MIT License.
