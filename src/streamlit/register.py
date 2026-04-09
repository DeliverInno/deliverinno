import streamlit as st
import requests
from src.streamlit.config import API_URL
from typing import Literal

st.title = "Register page"


def register(username: str, password: str, role: Literal["buyer", "seller"] | str):
    if not username or not password:
        st.error("Fill all fields")
    else:
        with st.spinner("Registering..."):
            try:
                data = {
                    "username": username,
                    "password": password,
                    "role": role
                }

                response = requests.post(
                    f"{API_URL}/auth/register",
                    json=data,
                    timeout=5
                )

                if response.status_code == 201:
                    result = response.json()
                    st.session_state.access_token = result.get('access_token')
                    st.session_state.role = result.get('role')
                    st.session_state.logged_in = True
                    st.rerun()
                elif response.status_code == 400:
                    error = response.json()
                    st.error(f"{error}")
                else:
                    st.error(f"Server error: {response.status_code}")
            except requests.exceptions.Timeout:
                st.error("Request timeout. Try again.")
            except requests.exceptions.ConnectionError:
                st.error("Connection error. Check your internet.")
            except Exception as e:
                st.error(f"Error: {str(e)}")


def show_register():
    with st.form("register", border=True):
        username = st.text_input("Username", icon=":material/person:")
        password = st.text_input("Password", type="password",
                                 icon=":material/password:")
        role = st.selectbox("Choose role", ["buyer", "seller"])
        submit = st.form_submit_button("Register", icon=":material/login:",
                                       type="primary", use_container_width=True)

        if submit:
            register(username, password, role)

    if st.button("Already have account? Login", width="stretch"):
        st.session_state.page = "login"
        st.rerun()
