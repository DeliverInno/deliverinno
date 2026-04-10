import pytest
from streamlit.testing.v1 import AppTest
from unittest.mock import patch


@pytest.fixture
def app_test():
    return AppTest.from_file("src/streamlit/login.py")


def test_login_form_renders(app_test):
    at = app_test.run()
    assert len(at.text_input) >= 2
    assert at.text_input[0].label == "Username"
    assert at.text_input[1].label == "Password"
    assert at.button[0].label == "Login"
    assert at.button[1].label == "Don't have account? Register!"


def test_empty_fields_error(app_test):
    at = app_test.run()
    at.button[0].click().run()
    assert at.error[0].value == "Fill all fields"


@patch("src.streamlit.login.requests.post")
def test_successful_login_updates_session(mock_post, app_test):
    mock_response = mock_post.return_value
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "tok", "role": "buyer"}

    at = app_test.run()
    at.text_input[0].input("user").run()
    at.text_input[1].input("pass").run()
    at.button[0].click().run()

    assert at.session_state["logged_in"] is True
    assert at.session_state["access_token"] == "tok"
    assert not at.exception


@patch("src.streamlit.login.requests.post")
def test_login_invalid_credentials_shows_error(mock_post, app_test):
    mock_response = mock_post.return_value
    mock_response.status_code = 401
    mock_post.return_value = mock_response

    at = app_test.run()
    at.text_input[0].input("wrong").run()
    at.text_input[1].input("pass").run()
    at.button[0].click().run()

    assert at.error[0].value == "Invalid credentials"


def test_register_button_changes_page(app_test):
    at = app_test.run()
    at.button[1].click().run()
    assert at.session_state["page"] == "register"
