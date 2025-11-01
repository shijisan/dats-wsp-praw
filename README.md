**Data sources:**

* Google Trends → pytrends (limited, often unreliable)
* Reddit → PRAW (best option)
* Reddit Pushshift → requires moderator access
* Twitter → too volatile

**Modeling:**

* LSTM → needs large datasets
* Prophet → works well for smaller datasets

**Things to consider:**

* Partial-day bias in data

**Features:**

* Predict trends based on week/month intervals
* Fetch trending topics by location

**Setup:**

1. `cd` into the `backend` folder
2. Activate your virtual environment
3. `pip install -r requirements.txt`
4. Add your Reddit client ID and secret to `.env`
5. Run `uvicorn` to serve the backend
6. Access the API via frontend (`npm run dev`)

**To Be Added:**

1. Chart JS
2. Better UI and Colors