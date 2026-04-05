import streamlit as st
import requests
from src.shared.models.buyer import ProductResponse
from src.shared.models.seller import ProductCreate, ProductUpdate
from streamlit_app import API_URL


def updateProduct(product_id: int, name: str, description: str, price: float, quantity: int):
    headers = {"Authorization Bearer": str(st.session_state.access_token)}
    try:
        res = requests.put(
            f"{API_URL}/seller/products/{product_id}",
            json=ProductUpdate(
                name=name, description=description, price=price, quantity=quantity).model_dump(),
            headers=headers,
            timeout=5
        )

        if res.status_code == 200:
            st.toast(f"Updated product {name}")
            st.rerun()
        else:
            st.error(f"Error: {res.status_code}")

    except Exception as e:
        st.error(f"Connection failed: {e}")


def deleteProduct(product_id: int):
    headers = {"Authorization Bearer": str(st.session_state.access_token)}
    try:
        res = requests.delete(
            f"{API_URL}/seller/products/{product_id}",
            headers=headers,
            timeout=5
        )

        if res.status_code == 204:
            st.toast(f"Removed product {name}")
            st.rerun()
        else:
            st.error(f"Error: {res.status_code}")

    except Exception as e:
        st.error(f"Connection failed: {e}")


def createProduct(name: str, description: str, price: float, quantity: int):
    headers = {"Authorization Bearer": str(st.session_state.access_token)}
    try:
        res = requests.post(
            f"{API_URL}/seller/products",
            json=ProductCreate(
                name=name, description=description, price=price, quantity=quantity).model_dump(),
            headers=headers,
            timeout=5
        )

        if res.status_code == 201:
            st.toast(f"Created product {name}")
            st.rerun()
        else:
            st.error(f"Error: {res.status_code}")

    except Exception as e:
        st.error(f"Connection failed: {e}")


COLS = 2

cols = st.columns(COLS, width="stretch")


st.popover("Add new product")
with st.form("add_product"):
    name = st.text_input("Name")
    desc = st.text_input("Description")
    price = st.number_input("Price")
    qt = st.number_input("Quantity", step=1)
    submit = st.form_submit_button("Create")
    if submit:
        if not name or not desc or not price or not qt:
            st.error("Fill all fields")
        else:
            createProduct(name, desc, price, qt)


with st.spinner("Loading..."):
    headers = {"Authorization Bearer": str(st.session_state.access_token)}
    response = requests.get(
        f"{API_URL}/seller/products",
        headers=headers,
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
                        with st.popover("Edit", use_container_width=True):
                            with st.form(f"product_{product.id}"):
                                name = st.text_input("Name", value=product.name)
                                desc = st.text_input("Description", value=product.description)
                                price = st.number_input("Price", value=product.price)
                                qt = st.number_input("Quantity", value=product.quantity)
                                submit = st.form_submit_button("Update")
                                if submit:
                                    if not name or not desc or not price or not qt:
                                        st.error("Fill all fields")
                                    else:
                                        updateProduct(product.id, name, desc, price, qt)
    else:
        st.error(response.json().get('detail'))
