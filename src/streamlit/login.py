import streamlit as st
import requests

from src.streamlit.config import API_URL


def login(username: str, password: str):
    # Validate input early to avoid unnecessary network calls
    if not username or not password:
        st.error("Fill all fields")
    else:
        with st.spinner("Login..."):
            try:
                data = {
                    "username": username,
                    "password": password,
                }

                # POST credentials to auth endpoint (timeout to avoid hanging UI)
                response = requests.post(
                    f"{API_URL}/auth/login",
                    json=data,
                    timeout=5
                )

                if response.status_code == 200:
                    # Store tokens/role in session state for later requests and UI control
                    result = response.json()
                    st.session_state.access_token = result.get('access_token')
                    st.session_state.role = result.get('role')
                    st.session_state.logged_in = True
                    st.rerun()  # refresh app to reflect logged-in state
                elif response.status_code == 401:
                    st.error("Invalid credentials")
                elif response.status_code == 400:
                    # show validation detail from API if available
                    error = response.json()
                    st.error(f"{error.get('detail').get('msg')}")
                else:
                    st.error(f"Server error: {response.status_code}")
            except requests.exceptions.Timeout:
                st.error("Request timeout. Try again.")
            except requests.exceptions.ConnectionError:
                st.error("Connection error. Check your internet.")
            except Exception as e:
                st.error(f"Error: {str(e)}")


def show_login():
    # Use a form so submit is explicit and input state is grouped
    with st.form(key="login", border=True):
        username = st.text_input("Username", icon=":material/person:")
        password = st.text_input("Password", type="password", icon=":material/password:")
        submit = st.form_submit_button("Login", icon=":material/login:",
                                       type="primary", use_container_width=True)
        if submit:
            login(username, password)

    # Button outside form to switch to registration page
    if st.button("Don't have account? Register!", width="stretch"):
        st.session_state.page = "register"
        st.rerun()


if __name__ == "__main__":
    show_login()
