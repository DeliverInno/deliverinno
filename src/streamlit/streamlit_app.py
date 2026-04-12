import streamlit as st
import sys
from pathlib import Path

from src.streamlit.buyer.buyer_catalog import show_catalog
from src.streamlit.buyer.cart import show_cart
from src.streamlit.buyer.orders import show_orders
from src.streamlit.login import show_login
from src.streamlit.register import show_register
from src.streamlit.seller.dashboard import show_dashboard


# Add project root to Python path to enable absolute imports
sys.path.insert(0, str(Path(__file__).parent))

# Initialize session state variables that persist across reruns
# These track user authentication status, current page, and user role
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"
if "role" not in st.session_state:
    st.session_state.role = "none"


def logout():
    # Handle logout button click and reset user session
    if st.button("Log out"):
        # Mark user as logged out to trigger navigation redirect
        st.session_state.logged_in = False
        # Reset role to prevent unauthorized access if session persists
        st.session_state.role = "none"
        # Rerun app to navigate back to login page
        st.rerun()


# Set the main title displayed at the top of the app
st.title = "DeliverInno"


# Define page objects for unauthenticated users (login/register)
login_page = st.Page(show_login, title="Log in", icon=":material/login:")
register_page = st.Page(show_register, title="Register", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

# Define page objects for authenticated buyers
# default=True makes "Catalog" the landing page when buyer logs in
buyer_catalog = st.Page(
    show_catalog, title="Catalog", icon=":material/dashboard:", default=True
)
shopping_cart = st.Page(show_cart, title="Shopping cart", icon=":material/shopping_cart:")
orders = st.Page(show_orders, title="Order history", icon=":material/orders:")

# Define page objects for authenticated sellers
# default=True makes "Dashboard" the landing page when seller logs in
dashboard = st.Page(show_dashboard, title="Dashboard",
                    icon=":material/dashboard_2_gear:", default=True)

# Conditional navigation based on user authentication status and role
# This determines which pages appear in the sidebar and which page loads
if st.session_state.logged_in:
    # User is authenticated; show role-specific navigation
    if st.session_state.role == "buyer":
        # Buyer navigation with catalog, cart, and order history
        pg = st.navigation(
            {
                "Account": [logout_page],
                "Browse": [buyer_catalog, shopping_cart, orders],
            }
        )
    else:
        # Seller navigation with dashboard only
        pg = st.navigation(
            {
                "Account": [logout_page],
                "Browse": [dashboard],
            }
        )
else:
    # User is not authenticated; show login/register pages only
    if st.session_state.page == "register":
        # User clicked "Sign up" link; show registration page
        pg = st.navigation([register_page])
    else:
        # Default to login page for unauthenticated users
        pg = st.navigation([login_page])

# Execute the navigation and render the selected page
pg.run()
