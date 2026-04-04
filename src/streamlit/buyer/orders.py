import streamlit as st
import requests
from src.shared.models.buyer import OrderResponse
from streamlit_app import API_URL


COLS = 2

cols = st.columns(COLS, width="stretch")


with st.spinner("Loading..."):
    headers = {"X-User-Id": str(st.session_state.id)}
    response = requests.get(f"{API_URL}/buyer/orders", headers=headers,
                            timeout=5)

    if response.status_code == 200:
        orders = [OrderResponse(**item) for item in response.json()]
        for i in range(0, len(orders), COLS):
            row = orders[i: i + COLS]
            for c, order in zip(cols, row):
                with c:
                    box = c.container(border=True)
                    with box:
                        st.header(f"# {order.id}")
                        st.write(f"## Status: {order.status}")
                        for item in order.items:
                            st.write(
                                f"- {item.product_id} x{item.quantity} for {item.price_at_time}")
