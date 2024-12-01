# Order Management Service

Simulation of an order matching system, allowing users to place, fetch, modify, and cancel orders. It also broadcasts updates via WebSockets.

### Prerequisites

- Docker
- Docker Compose
- Python
- Postman (for API testing)

### Installing and Running

1. **Clone the repository** to your local machine:
```bash
git clone https://github.com/DhruvAjayToshniwal/Order-API.git
cd repository
```

2. **Build and run the Docker container:**
```bash
docker-compose up --build
```

This command builds the Docker image and starts the application. The API will be accessible at `http://localhost:8000`.

### Testing with Postman

1. **Import the Postman Collection**:

- Open Postman.
- Click on `Import` button.
- Choose the provided Postman Collection file (`.json`) and import it.

2. **Setting Up Environment Variables in Postman**:

- In Postman, go to the Environments tab on the left sidebar.
- Click the Add button to create a new environment.
- Name your environment (e.g., Order Management).
- Add the following variables:
`order_id` with no initial value (this will be set dynamically).

## Using the Postman Collection for Testing

After importing the Postman Collection into your Postman workspace, follow these steps to test the API:

### Placing a New Order

1. **Send a POST request to create an order**:
   - Select the `POST /order/` request from the collection.
   - In the body of the request, input the details of the order you wish to place. Example body:
     ```json
     {
       "quantity": 10,
       "price": 100.0,
       "side": 1
     }
     ```
   - Hit send, and you should receive a response including the `id` of the created order.

### Fetching an Order

2. **Fetch the details of an existing order**:
   - Select the `GET /order/{{order_id}}` request from the collection.
   - Set the `order_id` variable in Postman to the ID of the order you wish to fetch. You can set the variable in the `Params` tab or directly in the URL.
   - Send the request, and you should receive the details of the specified order.

### Modifying an Order

3. **Modify an existing order**:
   - Choose the `PUT /order/{{order_id}}` request.
   - Ensure the `order_id` variable is set to the ID of the order you wish to modify.
   - In the request body, specify the new `quantity` and/or `price` for the order.
     ```json
     {
       "quantity": 15,
       "price": 105.0
     }
     ```
   - Send the request, and you should receive confirmation that the order has been updated.

### Cancelling an Order

4. **Cancel an order**:
   - Select the `DELETE /order/{{order_id}}` request.
   - Set the `order_id` variable to the ID of the order you wish to cancel.
   - Send the request, and you should receive confirmation that the order has been cancelled.

### Environment Variables

- Ensure you have set up your Postman Environment with the variable `order_id` to easily manage order IDs across requests.
- You can add or modify environment variables by selecting the environment settings in Postman and adding key-value pairs.

### Automation

- To automate fetching the `order_id` from the create order response and using it in subsequent requests, you can use Postman's test scripts to extract the `id` from the response and set it as an environment variable. Here's a simple script you can add to the "Tests" tab of the `POST /order/` request:

  ```json
  let responseData = pm.response.json();
  pm.environment.set("order_id", responseData.id);

## Docker Compose

The `docker-compose.yml` file defines the application's services, networks, and volumes. This file ensures that the Docker container has everything it needs to run the application.

## Shutting Down

To stop and remove the containers, networks, and volumes created by `docker-compose up`, run:

```bash
docker-compose down
```

## Restoring Application State

The application saves its state periodically to a file named `order_book_state.json`. Upon restart, it attempts to load this file to restore its state. Ensure this file is present in the application directory if you wish to preserve the application state between restarts.
