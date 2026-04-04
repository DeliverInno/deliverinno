import streamlit as st
import requests
from src.shared.models.buyer import AddToCartRequest, ProductResponse
from streamlit_app import API_URL


def addToCart(product_id: int, count: int):
    headers = {"X-User-Id": str(st.session_state.id)}
    try:
        res = requests.post(
            f"{API_URL}/buyer/cart",
            json=AddToCartRequest(
                product_id=product_id, quantity=count).model_dump(),
            headers=headers,
            timeout=5
        )

        if res.status_code == 201:
            st.toast(f"Added {count} to cart!")
            st.rerun()
        elif res.status_code == 400:
            st.error("Not enough stock!")
        else:
            st.error(f"Error: {res.status_code}")

    except Exception as e:
        st.error(f"Connection failed: {e}")


COLS = 2

cols = st.columns(COLS, width="stretch")


with st.spinner("Loading..."):
    response = requests.get(
        f"{API_URL}/buyer/products",
        timeout=5
    )

    if response.status_code == 200:
        products = [ProductResponse(**item) for item in response.json()]
        for i in range(0, len(products), COLS):
            row = products[i: i + COLS]
            for c, product in zip(cols, row):
                with c:
                    box = c.container(border=True)
                    with box:
                        st.header(product.name)
                        st.write(f"### {product.description}")
                        st.write(f"#### Quantity: {product.quantity}")
                        st.write(f"## {product.price} $")
                        with st.popover("Add to cart", use_container_width=True):
                            count = st.number_input(
                                "Quantity",
                                min_value=1,
                                max_value=product.quantity,
                                key=f"num_{product.id}"
                            )
                            if st.button("Confirm", key=f"btn_{product.id}", type="primary"):
                                addToCart(product.id, count)
