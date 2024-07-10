import streamlit as st
import requests

backend_url = "http://localhost:8000"

def signup():
    st.title("Sign Up")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    email = st.text_input("Email")
    full_name = st.text_input("Full Name")

    if st.button("Sign Up"):
        if username and email and full_name and password:
            response = requests.post(f"{backend_url}/users/new", json={
                "username": username,
                "email": email,
                "full_name": full_name,
                "password": password
            })
            if response.status_code == 200:
                st.success("User created successfully!")
            elif response.status_code == 400:
                st.error("Username already exists")
            else:
                st.error("Error creating user")

def login():
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username and password:
            response = requests.post(f"{backend_url}/token", data={
                "username": username,
                "password": password
            })
            if response.status_code == 200:
                st.success("Login successful!")
                st.session_state["token"] = response.json()["access_token"]
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
            elif response.status_code == 401:
                st.error("Incorrect username or password")
            else:
                st.error("Error logging in")

def main():
    if "token" not in st.session_state:
        st.session_state["token"] = None

    st.sidebar.title("Navigation")
    choice = st.sidebar.radio("Go to", ["Login", "Sign Up"])

    if choice == "Sign Up":
        signup()
    elif choice == "Login":
        login()


if __name__ == "__main__":
    main()
