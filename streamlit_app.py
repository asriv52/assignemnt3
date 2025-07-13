import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from transformers import pipeline

def toi(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            st.error(f"Failed to fetch the page. Status code: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "lxml")
        st.success("TOI page loaded successfully!")

        #title
        title_tag = soup.find("h1")
        title = title_tag.text.strip() if title_tag else "No title found"

        #article
        paragraphs = soup.find_all("div", class_="_s30J clearfix")
        if not paragraphs:
            paragraphs = soup.find_all("div", class_="_s30J")

        article_text = " ".join(p.get_text(strip=True) for p in paragraphs)

        if not article_text:
            article_text = soup.get_text()

        #date
        try:
            date_tag = soup.find("div", class_="xf8Pm byline").find("span")
            date = date_tag.get_text(strip=True).replace("Updated: ", "") if date_tag else "No date available"
        except:
            date = "No date available"

        #summarize
        with st.spinner("Summarizing article..."):
            summary = summarizer(article_text[:1024], max_length=150, min_length=100, do_sample=False)[0]['summary_text']

        return [{"Title": title, "URL": url, "Date": date, "Summary": summary}]

    except Exception as e:
        st.error(f"An error occurred while scraping Times of India: {e}")
        return []
    
def bbc(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            st.error(f"Failed to fetch the page. Status code: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "lxml")
        st.success("BBC page loaded successfully!")

        #title
        title_tag = soup.find("h1")
        title = title_tag.text.strip() if title_tag else "No title found"

        #article
        paragraphs = soup.find_all("p", class_="sc-9a00e533-0 hxuGS")
        article_text = " ".join(p.get_text(strip=True) for p in paragraphs)

        if not article_text:
            article_text = soup.get_text()
        
        #date
        try:
            date_tag = soup.find("time")
            date = date_tag["datetime"] if date_tag and date_tag.has_attr("datetime") else date_tag.get_text(strip=True)
        except:
            date = "No date available"

        #summarize
        with st.spinner("Summarizing article..."):
            summary = summarizer(article_text[:1024], max_length=150, min_length=100, do_sample=False)[0]['summary_text']

        return [{"Title": title, "URL": url, "Date": date, "Summary": summary}]

    except Exception as e:
        st.error(f"An error occurred while scraping BBC: {e}")
        return []

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
st.title("Article Scraper & Summarizer")
source = st.radio("Choose a news source:", ["Times of India", "BBC"])

url = st.text_input("Enter the URL of the article:")

if st.button("Summarize"):
    if url:
        if source == "Times of India":
            data = toi(url)
        else:
            data = bbc(url)

        if data:
            microlink_url = f"https://api.microlink.io/?url={url}&screenshot=true&meta=true"
            response = requests.get(microlink_url)
            article_data = response.json()["data"]
                
            #screenshot and link using microlink
            st.image(article_data["screenshot"]["url"], caption="Article Preview", use_container_width=True)
            st.link_button("Read Full Article", article_data["url"])

            for article in data:
                st.markdown("**Summary:**")
                st.info(article["Summary"])
                st.markdown("---")
            df = pd.DataFrame(data)
            st.dataframe(df)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(label="Download as CSV", data=csv, file_name="article_data.csv", mime="text/csv")

            if st.button("Reset"):
                st.experimental_rerun()
    else:
        st.error("Please enter a valid URL.")

