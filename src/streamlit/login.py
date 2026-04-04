import streamlit as st
import requests
from streamlit_app import API_URL

st.title = "Login page"


def login(username: str, password: str):
    if not username or not password:
        st.error("Fill all fields")
    else:
        with st.spinner("Login..."):
            try:
                data = {
                    "username": username,
                    "password": password,
                }

                response = requests.post(
                    f"{API_URL}/auth/login",
                    json=data,
                    timeout=5
                )

                if response.status_code == 200:
                    result = response.json()
                    st.session_state.id = result.get('id')
                    st.session_state.role = result.get('role')
                    st.session_state.logged_in = True
                    st.rerun()
                elif response.status_code == 401:
                    st.error("Invalid credentials")
                elif response.status_code == 400:
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


with st.form("login", border=True):
    username = st.text_input("Username", icon=":material/person:")
    password = st.text_input("Password", type="password", icon=":material/password:")
    submit = st.form_submit_button("Login", icon=":material/login:",
                                   type="primary", use_container_width=True)
    if submit:
        login(username, password)

if st.button("Don't have account? Register!", width="stretch"):
    st.session_state.page = "register"
    st.rerun()
