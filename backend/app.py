from numpy import int_
import praw
import math
import calendar
from datetime import datetime
import pandas as pd
from prophet import Prophet
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Literal, Optional, Mapping
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ForecastRequest(BaseModel):
    keyword: str
    time_frame: str
    method: Literal["log", "linear"]
    days_to_predict: int

@app.get("/")
def test():
    print("API is working")
    return {"message": "API is working"}


@app.post("/predict")
def forecast(req: ForecastRequest):
    result: Optional[Mapping[str, pd.DataFrame]] = fetch_praw_data(
        req.keyword, req.time_frame, req.method, req.days_to_predict
    )
    if result is None:
        return JSONResponse(content={"error": "no forecast data"}, status_code=404)

    historical = result["historical"]
    future = result["future"]
    historical = historical.sort_values("ds")
    future = future.sort_values("ds")

    for df in [historical, future]:
        df["ds"] = df["ds"].dt.strftime("%Y-%m-%dT%H:%M:%S")

    return JSONResponse({
        "historical": historical.to_dict(orient="records"),
        "forecast": future.to_dict(orient="records")
    })

load_dotenv()

reddit = praw.Reddit(
    client_id= os.getenv("CLIENT_ID"),
    client_secret= os.getenv("CLIENT_SECRET"),
    user_agent="dats-wsp:v1.0"
)

time_frame_selection = {"week", "month", "year"}

def linear_normalize(x, min_x, max_x):
    if max_x == min_x:
        return 0
    return (x - min_x) / (max_x - min_x)

def log_normalize(x, min_x, max_x):
    log_x = math.log1p(x)
    log_min = math.log1p(min_x)
    log_max = math.log1p(max_x)
    if log_max == log_min:
        return 0
    return (log_x - log_min) / (log_max - log_min)

def fetch_praw_data(
    keyword: str,
    time_frame: str,
    method="log",
    days_to_predict: int = 1
) -> Optional[Mapping[str, pd.DataFrame]]:
    if not keyword or not time_frame or time_frame not in time_frame_selection:
        return None

    now = datetime.now()
    limit_calc = {
        "week": 7 * 10,
        "month": calendar.monthrange(now.year, now.month)[1] * 10,
        "year": (366 if calendar.isleap(now.year) else 365) * 10,
    }[time_frame]

    posts = []
    for post in reddit.subreddit("all").search(keyword, limit=limit_calc, time_filter=time_frame):
        posts.append({"ds": datetime.fromtimestamp(post.created_utc), "score": post.score})

    if not posts:
        return None

    scores = [p["score"] for p in posts]
    min_score, max_score = min(scores), max(scores)

    for p in posts:
        normalized = log_normalize(p["score"], min_score, max_score) if method == "log" else linear_normalize(p["score"], min_score, max_score)
        p["y"] = round(normalized * 100, 2)

    # raw normalized historical dataframe
    df = pd.DataFrame(posts)
    df["ds"] = pd.to_datetime(df["ds"]).dt.normalize()
    df = df.groupby("ds", as_index=False).agg({"y": "mean"})
    df = pd.DataFrame(df)  # <- force Pyright to see this as DataFrame
    df = df.astype({"y": "float"})
    df.rename(columns={"y": "yhat"}, inplace=True)



    # future forecast with Prophet
    future_forecast = pd.DataFrame()
    if days_to_predict > 0:
        m = Prophet()
        m.fit(df.rename(columns={"yhat": "y"}))  # Prophet expects column 'y'
        future = m.make_future_dataframe(periods=days_to_predict)
        future_forecast = m.predict(future)
        future_forecast = future_forecast[future_forecast["ds"] > df["ds"].max()][["ds", "yhat", "yhat_lower", "yhat_upper"]]

    return {
        "historical": pd.DataFrame(df),
        "future": pd.DataFrame(future_forecast),
    }



def predict(df, days_to_predict):
    m = Prophet()
    m.fit(df)
    if days_to_predict <= 0:
        print("days to predict must be greater than 0")
        return
    future = m.make_future_dataframe(periods=days_to_predict)
    forecast = m.predict(future)
    last_date = df["ds"].max()
    historical_forecast = forecast[forecast["ds"] <= last_date].copy()
    future_forecast = forecast[forecast["ds"] > last_date].copy()
    cols = ["ds", "yhat", "yhat_lower", "yhat_upper"]
    historical_forecast = historical_forecast[cols]
    future_forecast = future_forecast[cols]

    return {
        "historical": historical_forecast,
        "future": future_forecast,
    }
    # print(forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]])

