import pytest
from streamlit.testing.v1 import AppTest
from unittest.mock import patch


@pytest.fixture
def app_test():
    return AppTest.from_file("src/streamlit/register.py")


def test_register_page_renders_fields(app_test):
    at = app_test.run()
    assert len(at.text_input) >= 2
    assert at.selectbox[0].label == "Choose role"
    assert at.button[0].label == "Register"
    assert at.button[1].label == "Already have account? Login"


def test_empty_fields_error(app_test):
    at = app_test.run()
    at.button[0].click().run()
    assert at.error[0].value == "Fill all fields"


@patch("src.streamlit.register.requests.post")
def test_register_success_seller(mock_post, app_test):
    mock_response = mock_post.Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"access_token": "newtoken", "role": "seller"}
    mock_post.return_value = mock_response

    at = app_test.run()
    at.text_input[0].input("newuser").run()
    at.text_input[1].input("pass").run()
    at.selectbox[0].select("seller").run()
    at.button[0].click().run()

    assert at.session_state["logged_in"] is True
    assert at.session_state["role"] == "seller"


@patch("src.streamlit.register.requests.post")
def test_register_success_buyer(mock_post, app_test):
    mock_response = mock_post.Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"access_token": "newtoken", "role": "buyer"}
    mock_post.return_value = mock_response

    at = app_test.run()
    at.text_input[0].input("newuser").run()
    at.text_input[1].input("pass").run()
    at.selectbox[0].select("buyer").run()
    at.button[0].click().run()

    assert at.session_state["logged_in"] is True
    assert at.session_state["role"] == "buyer"


@patch("src.streamlit.register.requests.post")
def test_register_validation_error(mock_post, app_test):
    mock_response = mock_post.Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": "test"}
    mock_post.return_value = mock_response

    at = app_test.run()
    at.text_input[0].input("newuser").run()
    at.text_input[1].input("pass").run()
    at.selectbox[0].select("buyer").run()
    at.button[0].click().run()

    assert at.error[0].value == "{'error': 'test'}"
