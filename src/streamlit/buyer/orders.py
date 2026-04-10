import streamlit as st
import requests
from src.shared.models.buyer import OrderResponse
from src.streamlit.config import API_URL


# Number of order cards to display per row in the dashboard grid
COLS = 2


def show_orders():
    # Initialize column objects for 2-column layout
    # Must be created outside spinner to persist across st.rerun() calls
    cols = st.columns(COLS, width="stretch")

    # Show loading spinner while fetching orders from API
    with st.spinner("Loading..."):
        try:
            # Prepare authorization header with JWT token from session state
            headers = {"Authorization": f"Bearer {st.session_state.access_token}"}

            # Fetch all orders for the current buyer from the API
            response = requests.get(
                f"{API_URL}/buyer/orders",
                headers=headers,
                timeout=5  # 5 second timeout to prevent hanging requests
            )

            # HTTP 200 indicates successful response with order data
            if response.status_code == 200:
                # Parse JSON response into OrderResponse Pydantic models
                orders = [OrderResponse(**item) for item in response.json()]

                # Split orders into rows of COLS elements and render in grid layout
                # Loop increments by COLS (2), so i = [0, 2, 4, 6, ...]
                for i in range(0, len(orders), COLS):
                    # Extract a slice of up to COLS orders for this row
                    row = orders[i: i + COLS]

                    # Zip orders with column objects so each order gets a column
                    for c, order in zip(cols, row):
                        # Render order card in current column
                        with c:
                            # Container with border provides visual separation for each order
                            box = c.container(border=True)
                            with box:
                                # Display order ID as main heading
                                st.header(f"# {order.id}")

                                # Display order status (e.g., "pending", "completed", "shipped")
                                st.write(f"## Status: {order.status}")

                                # Iterate through all items in this order and display each one
                                for item in order.items:
                                    # Show item name, quantity ordered, and price paid
                                    # (price_at_time may differ from current product price)
                                    st.write(
                                        f"- {item.name} x{item.quantity} for {item.price_at_time}$")
            else:
                # Display error message if API request returns non-200 status code
                st.error(f"Failed to load orders. Server returned {response.status_code}")

        except Exception as e:
            # Catch network errors, timeouts, and other request failures
            st.error(f"Connection error: {e}")


# Run the orders dashboard when script is executed directly
if __name__ == "__main__":
    show_orders()
