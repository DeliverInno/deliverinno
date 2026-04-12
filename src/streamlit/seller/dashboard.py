import streamlit as st
import requests
from src.shared.models.buyer import ProductResponse
from src.shared.models.seller import ProductCreate, ProductUpdate
from src.streamlit.config import API_URL

# Update an existing product via the seller API.


def updateProduct(product_id: int, name: str, description: str, price: float, quantity: int):
    # Validate all required fields before making API call
    if not name or not description or not price or not quantity:
        st.error("Fill all fields")

    # Prepare authorization header with JWT token from session state
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    try:
        # Send PUT request to update product on backend
        res = requests.put(
            f"{API_URL}/seller/products/{product_id}",
            # Convert Pydantic model to dict for JSON serialization
            json=ProductUpdate(
                name=name, description=description, price=price, quantity=quantity).model_dump(),
            headers=headers,
            timeout=5  # 5 second timeout to prevent hanging requests
        )

        # HTTP 200 indicates successful update
        if res.status_code == 200:
            st.toast(f"Updated product {name}")
            # Rerun entire script to refresh product list and close edit popover
            st.rerun()
        else:
            # Log unexpected HTTP status codes for debugging
            st.error(f"Error: {res.status_code}")

    except Exception as e:
        # Catch network errors, timeouts, and other request failures
        st.error(f"Connection failed: {e}")


# Delete a product via the seller API.
def deleteProduct(product_id: int):
    # Prepare authorization header with JWT token from session state
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    try:
        # Send DELETE request to remove product from backend
        res = requests.delete(
            f"{API_URL}/seller/products/{product_id}",
            headers=headers,
            timeout=5  # 5 second timeout to prevent hanging requests
        )

        # HTTP 204 No Content indicates successful deletion (no response body)
        if res.status_code == 204:
            st.toast("Removed product")
            # Rerun entire script to refresh product list
            st.rerun()
        else:
            # Log unexpected HTTP status codes for debugging
            st.error(f"Error: {res.status_code}")

    except Exception as e:
        # Catch network errors, timeouts, and other request failures
        st.error(f"Connection failed: {e}")

# Create a new product via the seller API.


def createProduct(name: str, description: str, price: float, quantity: int):
    # Prepare authorization header with JWT token from session state
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    try:
        # Send POST request to create product on backend
        res = requests.post(
            f"{API_URL}/seller/products",
            # Convert Pydantic model to dict for JSON serialization
            json=ProductCreate(
                name=name, description=description, price=price, quantity=quantity).model_dump(),
            headers=headers,
            timeout=5  # 5 second timeout to prevent hanging requests
        )

        # HTTP 201 Created indicates successful resource creation
        if res.status_code == 201:
            st.toast(f"Created product {name}")
            # Rerun entire script to clear form and refresh product list
            st.rerun()
        else:
            # Log unexpected HTTP status codes for debugging
            st.error(f"Error: {res.status_code}")

    except Exception as e:
        # Catch network errors, timeouts, and other request failures
        st.error(f"Connection failed: {e}")


# Render a form for creating new products.
def _show_create_product_card():
    # Form groups inputs and only submits when submit button is clicked
    with st.form("add_product"):
        name = st.text_input("Name")
        desc = st.text_input("Description")
        price = st.number_input("Price")
        # step=1 ensures quantity increments by whole numbers only
        qt = st.number_input("Quantity", step=1)
        submit = st.form_submit_button("Create")

        # Only process submission if user clicked the submit button
        if submit:
            # Validate all required fields are filled
            if not name or not desc or not price or not qt:
                st.error("Fill all fields")
            else:
                # Call API to create product with validated inputs
                createProduct(name, desc, price, qt)

# Render a single product card with display info, delete button, and edit popover.


def _show_product_card(product: ProductResponse):
    # Display product name as main heading
    st.header(product.name)
    # Display description as subheading (markdown ### syntax)
    st.write(f"### {product.description}")
    # Display current stock quantity
    st.write(f"#### Quantity: {product.quantity}")
    # Display price prominently as ## heading
    st.write(f"## {product.price} $")

    # Delete button with unique key based on product ID to avoid widget key collisions
    # (critical when rendering multiple products in a loop)
    if st.button("Delete", key=f"del_{product.id}"):
        deleteProduct(product_id=product.id)

    # Popover widget opens edit form in a floating modal
    with st.popover("Edit", use_container_width=True):
        # Form widget with unique ID based on product ID to prevent form key conflicts
        with st.form(f"product_{product.id}"):
            # Pre-populate fields with current product values
            name = st.text_input("Name", value=product.name)
            desc = st.text_input("Description", value=product.description)
            # value parameter pre-fills the input with current product price
            price = st.number_input("Price", value=product.price)
            # value parameter pre-fills the input with current quantity
            qt = st.number_input("Quantity", value=product.quantity)
            submit = st.form_submit_button("Update")

            # Only process submission if user clicked the submit button
            if submit:
                # Convert description to string to match function signature
                # (may already be string, but ensures type consistency)
                updateProduct(product.id, name, str(desc), price, qt)


# Number of product columns to display per row in the dashboard grid
COLS = 2

# Main seller dashboard that displays all products in a grid layout.


def show_dashboard():
    # Initialize column objects for 2-column layout
    # Must be outside loop and outside spinner to persist across reruns
    cols = st.columns(COLS, width="stretch")

    # Render form for creating new products at the top of dashboard
    _show_create_product_card()

    # Show loading spinner while fetching products from API
    with st.spinner("Loading..."):
        # Prepare authorization header with JWT token from session state
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        try:
            # Fetch all products for the current seller from API
            response = requests.get(
                f"{API_URL}/seller/products",
                headers=headers,
                timeout=5  # 5 second timeout to prevent hanging requests
            )

            # HTTP 200 indicates successful response
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
                                # Render product UI (name, description, price, buttons)
                                _show_product_card(product)
            else:
                # Display error message if API request fails
                # Note: response object is being displayed directly instead of status code
                st.error(response)

        except Exception as e:
            # Catch network errors, timeouts, and other request failures
            # (this try/except is missing from the original code above)
            st.error(f"Failed to load products: {e}")


if __name__ == "__main__":
    # Run the dashboard when script is executed directly
    show_dashboard()
