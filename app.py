import streamlit as st
from deals_engine import get_top_deals
import requests
from io import BytesIO
from PIL import Image

# IMPORTANT: This must be the very first Streamlit command
st.set_page_config(page_title="🔥 Best Deals Finder", layout="wide")

# Everything else comes after st.set_page_config()
st.title("🛍️ Top Deals Gallery")

# --- Filter UI ---
st.sidebar.header("🔍 Filters")

platforms = st.sidebar.multiselect("Choose Platform(s)", ["amazon", "flipkart"], default=["amazon", "flipkart"])
min_discount = st.sidebar.slider("Minimum Discount (%)", 0, 100, 30)
min_rating = st.sidebar.slider("Minimum Rating", 1.0, 5.0, 3.5, step=0.1)
search_text = st.sidebar.text_input("Search by keyword", "")

limit = st.sidebar.slider("Number of top deals per platform", 5, 10, 10)

# --- Data Fetching ---
with st.spinner("Fetching and filtering deals..."):
    raw_results = get_top_deals(limit=limit)

    # Filter logic
    results = {}
    for platform, items in raw_results.items():
        if platform not in platforms:
            continue

        filtered = []
        for score, deal in items:
            name = deal.get("basic_info", {}).get("name", "").lower()
            discount = deal.get("pricing", {}).get("discount", {}).get("percentage", 0)
            rating = deal.get("ratings", {}).get("average", 3.0)

            if discount >= min_discount and rating >= min_rating and search_text.lower() in name:
                filtered.append((score, deal))

        results[platform] = filtered

# --- Display Cards ---
def display_deals(title, deals):
    st.subheader(title)
    cols = st.columns(2)
    for idx, (score, deal) in enumerate(deals):
        with cols[idx % 2]:
            name = deal.get("basic_info", {}).get("name", "Unnamed")
            url = deal.get("url", "#")
            pricing = deal.get("pricing", {})
            rating = deal.get("ratings", {}).get("average", None)

            current = pricing.get("current_price", {}).get("formatted", "₹-")
            original = pricing.get("original_price", {}).get("formatted", "₹-")
            discount = pricing.get("discount", {}).get("percentage", 0)
            savings = pricing.get("original_price", {}).get("amount", 0) - pricing.get("current_price", {}).get("amount", 0)

            # Enhanced image handling with proper error catching
            image_url = None
            if "image" in deal and deal["image"] and "url" in deal["image"]:
                image_url = deal["image"]["url"]
            elif "images" in deal and deal["images"] and len(deal["images"]) > 0 and "url" in deal["images"][0]:
                image_url = deal["images"][0]["url"]
            
            # Display image with proper error handling
            if image_url:
                try:
                    # Create a container for the image with fixed height
                    img_container = st.container()
                    with img_container:
                        st.image(image_url, use_column_width=True)
                except Exception as e:
                    st.error(f"Could not load image: {str(e)}")
                    # Fallback placeholder
                    st.markdown("📦 *Image unavailable*")

            # Product details
            st.markdown(f"### [{name}]({url})", unsafe_allow_html=True)
            
            # Create two columns for price info
            price_cols = st.columns([3, 2])
            with price_cols[0]:
                st.markdown(f"💰 **{current}** &nbsp;&nbsp; ~~{original}~~")
            with price_cols[1]:
                st.markdown(f"🎯 **{discount:.1f}%**")
            
            st.markdown(f"You save ₹{savings:.2f}")
            
            if rating:
                stars = "★" * int(round(rating)) + "☆" * (5 - int(round(rating)))
                st.markdown(f"⭐ {stars} ({rating:.1f}/5)")
            
            # Add a "View Deal" button
            if url and url != "#":
                st.markdown(f"[View Deal]({url})", unsafe_allow_html=True)
            
            st.markdown("---")

# --- Render Section ---
if not any(deals for platform, deals in results.items()):
    st.warning("No deals match your current filters. Try adjusting your criteria.")

for platform, deals in results.items():
    if deals:
        display_deals(f"🔥 Top {len(deals)} {platform.capitalize()} Deals", deals)
    else:
        st.info(f"No {platform} deals matched your filter.")

# Add a footer
st.markdown("---")
st.markdown("### 💡 Tips")
st.markdown("- Use the filters in the sidebar to narrow down your search")
st.markdown("- Click on product names or 'View Deal' to visit the product page")