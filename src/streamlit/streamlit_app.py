import os
import streamlit as st

API_URL = os.getenv('API_URL', "http://0.0.0.0:8000")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"
if "role" not in st.session_state:
    st.session_state.role = "none"


def login():
    if st.button("Log in"):
        st.session_state.logged_in = True
        st.session_state.role = "admin"
        st.rerun()


def logout():
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.session_state.role = "none"
        st.rerun()


st.title = "DeliverInno"


login_page = st.Page("login.py", title="Log in", icon=":material/login:")
register_page = st.Page("register.py", title="Register", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

buyer_catalog = st.Page(
    "buyer/buyer_catalog.py", title="Catalog", icon=":material/dashboard:", default=True
)
shopping_cart = st.Page("buyer/cart.py", title="Shopping cart", icon=":material/shopping_cart:")
orders = st.Page("buyer/orders.py", title="Order history", icon=":material/orders:")

dashboard = st.Page("seller/dashboard.py", title="Dashboard",
                    icon=":material/dashboard_2_gear:", default=True)

if st.session_state.logged_in:
    if st.session_state.role == "buyer":
        pg = st.navigation(
            {
                "Account": [logout_page],
                "Browse": [buyer_catalog, shopping_cart, orders],
            }
        )
    else:
        pg = st.navigation(
            {
                "Account": [logout_page],
                "Browse": [dashboard],
            }
        )
else:
    if st.session_state.page == "register":
        pg = st.navigation([register_page])
    else:
        pg = st.navigation([login_page])

pg.run()
