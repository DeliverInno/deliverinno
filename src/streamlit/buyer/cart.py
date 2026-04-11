import streamlit as st
import requests
from src.shared.models.buyer import CartItemResponse
from src.streamlit.config import API_URL

# Sends a POST to create an order for the current user.


def makeOrder():
    # Authorization header using the access token stored in session state.
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    try:
        res = requests.post(
            f"{API_URL}/buyer/orders",
            headers=headers,
            timeout=5  # short timeout to avoid blocking UI for too long
        )

        # 201 Created — success
        if res.status_code == 201:
            st.toast("Created order!")
            st.rerun()  # refresh UI to reflect the new state (e.g., empty cart)
        # 400 Bad Request — likely not enough stock for items in the cart
        elif res.status_code == 400:
            st.error("Not enough stock!")
        # Any other status is unexpected — show the status code for debugging
        else:
            st.error(f"Error: {res.status_code}")

    except Exception as e:
        # Network or other request-related error
        st.error(f"Connection failed: {e}")


COLS = 2  # number of product columns


def show_cart():
    # Create fixed number of columns once and reuse them when rendering rows
    cols = st.columns(COLS, width="stretch")

    with st.spinner("Loading..."):
        try:
            # Authorization header using the access token stored in session state.
            headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
            response = requests.get(
                f"{API_URL}/buyer/cart",
                headers=headers,
                timeout=5  # short timeout to avoid long waits in the UI
            )

            # Successful retrieval of cart items
            if response.status_code == 200:
                # Parse each item JSON into the CartItemResponse dataclass/model
                products = [CartItemResponse(**item) for item in response.json()]

                # Render products in rows of COLS columns
                for i in range(0, len(products), COLS):
                    row = products[i: i + COLS]
                    # zip stops when the shorter of the two iterables is exhausted;
                    # using the pre-created cols ensures consistent layout even on partial rows
                    for c, product in zip(cols, row):
                        with c:
                            # Use a container to visually group product info;
                            box = c.container(border=True)
                            with box:
                                st.header(product.name)                     # product title
                                st.write(f"#### Quantity: {product.quantity}")  # quantity in cart
                                st.write(f"### {product.price} $")             # price display

                # Show Make order button only if there are products
                if len(products) > 0:
                    if st.button("Make order", width="stretch", type="primary"):
                        makeOrder()
            else:
                # Non-200 response when fetching cart — helpful for debugging server issues
                st.error(f"Failed to load orders. Server returned {response.status_code}")
        except Exception as e:
            # Network or parsing error while loading the cart
            st.error(f"Connection error: {e}")


if __name__ == "__main__":
    show_cart()
