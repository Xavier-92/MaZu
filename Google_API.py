import requests
import streamlit as st
import os

def get_coordinates(address):
    api_key = st.secrets["google"]["api_key"]
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json().get('results')
        if results:
            location = results[0]['geometry']['location']
            return location['lat'], location['lng']
    return None, None

def read_excel(file_path):
    import pandas as pd
    if os.path.exists(file_path):
        return pd.read_excel(file_path)
    else:
        return pd.DataFrame()

def write_excel(file_path, df):
    import pandas as pd
    df.to_excel(file_path, index=False)

def validate_input(data):
    return all(data.values())  # Check if all values in the dictionary are non-empty

def format_address(address):
    return address.strip().replace(" ", "+")  # Format address for URL encoding

def log_error(error_message):
    import logging
    logging.error(error_message)  # Log error messages for debugging purposes
