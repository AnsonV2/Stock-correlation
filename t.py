import streamlit as st
from fastapi import FastAPI
from pymongo import MongoClient
import requests
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from scipy.stats import pearsonr
import uvicorn

app = FastAPI()

# MongoDB Setup
client = MongoClient("mongodb://localhost:27017/")
db = client["finance_data"]
collection = db["industry_correlation"]

# Gemini API Setup
GEMINI_API_KEY = "AIzaSyBOYvd7lVOfk8bMHs9rJWrJs9xmdPWYM3Q"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateText?key=" + GEMINI_API_KEY

def get_gemini_insight(sector1, sector2, period):
    prompt = f"Analyze correlations between {sector1} and {sector2} sectors during {period}. Summarize key economic events affecting them."
    response = requests.post(GEMINI_ENDPOINT, json={"contents": [{"parts": [{"text": prompt}]}]})
    if response.status_code == 200:
        return response.json()
    return {"error": "Failed to fetch insights"}

@app.get("/insights/{sector1}/{sector2}/{period}")
def insights(sector1: str, sector2: str, period: str):
    data = get_gemini_insight(sector1, sector2, period)
    return data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Data Collection & Correlation Analysis
def fetch_sector_data(tickers, period="6mo"):
    data = {}
    for sector, ticker in tickers.items():
        stock_data = yf.download(ticker, period=period, interval="1d")
        if not stock_data.empty:
            data[sector] = stock_data["Close"]
    return pd.DataFrame(data)

def calculate_correlations(df):
    correlation_matrix = df.corr(method='pearson')
    return correlation_matrix
#
@app.get("/correlations")
def correlations():
    tickers = {
        "Tech": "AAPL",
        "Finance": "JPM",
        "Energy": "XOM",
        "Healthcare": "PFE"
    }
    df = fetch_sector_data(tickers)
    correlation_matrix = calculate_correlations(df)
    collection.insert_one({"correlations": correlation_matrix.to_dict()})
    return correlation_matrix.to_dict()

# Streamlit UI
st.title("Industry Correlation & Insights")

if st.button("Compute Correlations"):
    correlation_result = requests.get("http://localhost:8000/correlations").json()
    st.write(pd.DataFrame(correlation_result))

sector1 = st.selectbox("Select First Sector", ["Tech", "Finance", "Energy", "Healthcare"])
sector2 = st.selectbox("Select Second Sector", ["Tech", "Finance", "Energy", "Healthcare"])
period = st.text_input("Enter Time Period (e.g., Q1 2024)")
if st.button("Get Gemini Insights"):
    insight_result = requests.get(f"http://localhost:8000/insights/{sector1}/{sector2}/{period}").json()
    st.write(insight_result)
