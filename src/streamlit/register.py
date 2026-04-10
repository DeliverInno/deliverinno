import streamlit as st
import requests
from src.streamlit.config import API_URL
from typing import Literal


def register(username: str, password: str, role: Literal["buyer", "seller"] | str):
    # Validate that username and password are not empty before API call
    if not username or not password:
        st.error("Fill all fields")
    else:
        # Show loading spinner while registration request is in progress
        with st.spinner("Registering..."):
            try:
                # Prepare registration payload with user credentials and role
                data = {
                    "username": username,
                    "password": password,
                    "role": role
                }

                # Send POST request to create new user account on backend
                response = requests.post(
                    f"{API_URL}/auth/register",
                    json=data,
                    timeout=5  # 5 second timeout to prevent hanging requests
                )

                # HTTP 201 Created indicates successful user registration
                if response.status_code == 201:
                    # Extract access token and role from successful registration response
                    result = response.json()
                    # Store JWT token in session state for future authenticated API requests
                    st.session_state.access_token = result.get('access_token')
                    # Store user role (buyer or seller) to control UI display later
                    st.session_state.role = result.get('role')
                    # Set logged_in flag to true so app redirects to main dashboard
                    st.session_state.logged_in = True
                    # Rerun entire app to redirect user to appropriate dashboard
                    st.rerun()

                # HTTP 400 Bad Request indicates validation error
                elif response.status_code == 400:
                    # Parse error details from server response
                    error = response.json()
                    # Display server-provided error message to user
                    st.error(f"{error}")

                # Any other status code indicates unexpected server error
                else:
                    st.error(f"Server error: {response.status_code}")

            # Handle request timeout separately for better UX messaging
            except requests.exceptions.Timeout:
                st.error("Request timeout. Try again.")

            # Handle connection errors separately for better UX messaging
            except requests.exceptions.ConnectionError:
                st.error("Connection error. Check your internet.")

            # Catch any other unexpected errors (JSON parsing, etc.)
            except Exception as e:
                st.error(f"Error: {str(e)}")


def show_register():
    # Form widget groups inputs and only submits when submit button is clicked
    with st.form("register", border=True):
        # Text input for username with person icon
        username = st.text_input("Username", icon=":material/person:")

        # Password input field (text is masked/hidden as user types)
        password = st.text_input("Password", type="password",
                                 icon=":material/password:")

        # Dropdown to select user role (buyer or seller) which affects feature access
        role = st.selectbox("Choose role", ["buyer", "seller"])

        # Submit button that triggers form submission
        submit = st.form_submit_button("Register", icon=":material/login:",
                                       type="primary", use_container_width=True)

        # Only process registration if user clicked the submit button
        if submit:
            # Call register function with validated form inputs
            register(username, password, role)

    # Clickable link for users who already have an account
    if st.button("Already have account? Login", width="stretch"):
        # Update session state to switch to login page
        st.session_state.page = "login"
        # Rerun app to render login page instead of register page
        st.rerun()


# Run the registration form when script is executed directly
if __name__ == "__main__":
    show_register()
