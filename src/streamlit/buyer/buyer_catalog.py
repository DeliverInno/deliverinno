import streamlit as st
import requests
from src.shared.models.buyer import AddToCartRequest, ProductResponse
from src.streamlit.config import API_URL


def addToCart(product_id: int, count: int):
    # Prepare authorization header with JWT token from session state
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    try:
        # Send POST request to add product to user's shopping cart
        res = requests.post(
            f"{API_URL}/buyer/cart",
            # Convert Pydantic model to dict for JSON serialization
            json=AddToCartRequest(
                product_id=product_id, quantity=count).model_dump(),
            headers=headers,
            timeout=5  # 5 second timeout to prevent hanging requests
        )

        # HTTP 201 Created indicates item was successfully added to cart
        if res.status_code == 201:
            # Show toast notification confirming item added with quantity
            st.toast(f"Added {count} to cart!")
            # Rerun to update cart UI and refresh product quantity display
            st.rerun()

        # HTTP 400 Bad Request typically means insufficient stock available
        elif res.status_code == 400:
            st.error("Not enough stock!")

        # Any other status code indicates unexpected error
        else:
            st.error(f"Error: {res.status_code}")

    # Catch network errors, timeouts, and other request failures
    except Exception as e:
        st.error(f"Connection failed: {e}")


# Number of product cards to display per row in the catalog grid
COLS = 2


def show_catalog():
    # Initialize column objects for 2-column layout
    # Must be created outside spinner to persist across st.rerun() calls
    cols = st.columns(COLS, width="stretch")

    # Show loading spinner while fetching product catalog from API
    with st.spinner("Loading..."):
        # Fetch all available products for the buyer from the API
        # No authentication header needed since catalog is publicly viewable
        response = requests.get(
            f"{API_URL}/buyer/products",
            timeout=5  # 5 second timeout to prevent hanging requests
        )

        # HTTP 200 indicates successful response with product data
        if response.status_code == 200:
            # Parse JSON response into ProductResponse Pydantic models
            products = [ProductResponse(**item) for item in response.json()]

            # Split products into rows of COLS elements and render in grid layout
            # Loop increments by COLS (2), so i = [0, 2, 4, 6, ...]
            for i in range(0, len(products), COLS):
                # Extract a slice of up to COLS products for this row
                row = products[i: i + COLS]

                # Zip products with column objects so each product gets a column
                for c, product in zip(cols, row):
                    # Render product card in current column
                    with c:
                        # Container with border provides visual separation for each product
                        box = c.container(border=True)
                        with box:
                            # Display product name as main heading
                            st.header(product.name)

                            # Display product description as subheading
                            st.write(f"### {product.description}")

                            # Display current stock quantity available
                            st.write(f"#### Quantity: {product.quantity}")

                            # Display product price prominently as heading
                            st.write(f"## {product.price} $")

                            # Expander widget collapses "Add to cart" section by default
                            # User clicks to expand and add items to cart
                            with st.expander("Add to cart", width="stretch"):
                                # Number input for selecting quantity to add
                                # min_value=1 prevents adding zero items
                                # max_value limits selection to available stock
                                # key=f"num_{product.id}" ensures unique widget ID in loop
                                count = st.number_input(
                                    "Quantity",
                                    min_value=1,
                                    max_value=product.quantity,
                                    key=f"num_{product.id}"
                                )

                                # Confirm button with unique key to prevent widget ID collisions
                                # type="primary" makes button stand out visually
                                if st.button("Confirm", key=f"btn_{product.id}", type="primary"):
                                    # Call addToCart with product ID and selected quantity
                                    addToCart(product.id, count)

        # Display error if API request returns non-200 status code
        else:
            st.error(f"Failed to load catalog. Status: {response.status_code}")


# Run the product catalog when script is executed directly
if __name__ == "__main__":
    show_catalog()
