# deals_engine.py
import pymongo
import heapq
from datetime import datetime

MONGODB_URI = "mongodb+srv://ss_dev_user:RHW0NjQrGdykt8PK@devlopment.sezrsj6.mongodb.net/?retryWrites=true&w=majority&appName=Devlopment&tls=true"
MONGODB_DATABASE = "scraperhive"
AMAZON_COLLECTION_NAME = "amazon_products"
FLIPKART_COLLECTION_NAME = "flipkart_products"

WEIGHTS = {'discount': 0.5, 'savings': 0.3, 'rating': 0.2}

class DealHeap:
    def __init__(self, max_size=10):
        self.max_size = max_size
        self.heap = []

    def add_deal(self, deal, score):
        deal_id = deal.get("platform_id", str(id(deal)))
        if len(self.heap) < self.max_size:
            heapq.heappush(self.heap, (-score, deal_id, deal))
        elif -score < self.heap[0][0]:
            heapq.heapreplace(self.heap, (-score, deal_id, deal))

    def get_top_deals(self):
        return [(-score, deal) for score, deal_id, deal in sorted(self.heap)]

def score_product(product):
    try:
        pricing = product.get("pricing", {})
        current_price = pricing.get("current_price", {}).get("amount", 0)
        original_price = pricing.get("original_price", {}).get("amount", 0)

        if current_price <= 0 or original_price <= 0 or current_price >= original_price:
            return 0

        discount = pricing.get("discount", {}).get("percentage")
        if discount is None:
            discount = ((original_price - current_price) / original_price) * 100

        savings = original_price - current_price
        rating = product.get("ratings", {}).get("average", 3.0)

        discount_score = discount * WEIGHTS['discount']
        savings_score = min(100, savings / 20) * WEIGHTS['savings']
        rating_score = (rating / 5 * 100) * WEIGHTS['rating']

        return discount_score + savings_score + rating_score
    except:
        return 0


def get_top_deals(limit=10):
    client = pymongo.MongoClient(MONGODB_URI)
    db = client[MONGODB_DATABASE]

    projection = {
        "platform": 1, "platform_id": 1, "basic_info.name": 1, "pricing": 1,
        "ratings": 1, "url": 1, "sales_info.best_sellers_rank": 1, "specifications.general": 1
    }
    filter_query = {
        "pricing.current_price.amount": {"$gt": 0},
        "pricing.original_price.amount": {"$gt": 0}
    }

    amazon_heap, flipkart_heap = DealHeap(limit), DealHeap(limit)

    for doc in db[AMAZON_COLLECTION_NAME].find(filter_query, projection).limit(200):
        score = score_product(doc)
        if score > 0:
            amazon_heap.add_deal(doc, score)

    for doc in db[FLIPKART_COLLECTION_NAME].find(filter_query, projection).limit(200):
        score = score_product(doc)
        if score > 0:
            flipkart_heap.add_deal(doc, score)

    client.close()
    return {"amazon": amazon_heap.get_top_deals(), "flipkart": flipkart_heap.get_top_deals()}


# app.py
import streamlit as st
from deals_engine import get_top_deals

st.set_page_config(page_title="🔥 Best Deals Finder", layout="wide")
st.title("🔥 Top Deals from Amazon & Flipkart")

limit = st.slider("How many top deals to show per platform?", min_value=5, max_value=50, value=10)

with st.spinner("Fetching top deals..."):
    results = get_top_deals(limit=limit)

def display_deals(title, deals):
    st.subheader(title)
    for score, deal in deals:
        name = deal.get("basic_info", {}).get("name", "[No title]")
        pricing = deal.get("pricing", {})
        cur = pricing.get("current_price", {})
        ori = pricing.get("original_price", {})
        url = deal.get("url", "")

        cur_amt = cur.get("amount")
        ori_amt = ori.get("amount")
        savings = ori_amt - cur_amt if ori_amt and cur_amt else 0
        discount = pricing.get("discount", {}).get("percentage") or ((ori_amt - cur_amt) / ori_amt * 100 if ori_amt else 0)

        st.markdown(f"#### 🛍️ [{name}]({url})")
        st.markdown(f"- 💰 **Price**: ₹{cur_amt} _(was ₹{ori_amt})_")
        st.markdown(f"- 📉 **Discount**: {discount:.1f}% | Savings: ₹{savings:.2f}")
        rating = deal.get("ratings", {}).get("average")
        if rating:
            st.markdown(f"- ⭐ **Rating**: {rating:.1f}/5")
        st.markdown("---")

if results["amazon"]:
    display_deals("🛒 Amazon Deals", results["amazon"])

if results["flipkart"]:
    display_deals("📦 Flipkart Deals", results["flipkart"])
