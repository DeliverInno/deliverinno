import streamlit as st
import requests
from src.shared.models.buyer import CartItemResponse
from streamlit_app import API_URL


def makeOrder():
    headers = {"Authorization Bearer": str(st.session_state.access_token)}
    try:
        res = requests.post(
            f"{API_URL}/buyer/orders",
            headers=headers,
            timeout=5
        )

        if res.status_code == 201:
            st.toast("Created order!")
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
    headers = {"Authorization Bearer": str(st.session_state.access_token)}
    response = requests.get(
        f"{API_URL}/buyer/cart",
        headers=headers,
        timeout=5
    )

    if response.status_code == 200:
        products = [CartItemResponse(**item) for item in response.json()]
        for i in range(0, len(products), COLS):
            row = products[i: i + COLS]
            for c, product in zip(cols, row):
                with c:
                    box = c.container(border=True)
                    with box:
                        st.header(product.name)
                        st.write(f"#### Quantity: {product.quantity}")
                        st.write(f"### {product.price} $")
        if st.button("Make order", width="stretch", type="primary"):
            makeOrder()
    else:
        st.error(response.json().get('detail'))
