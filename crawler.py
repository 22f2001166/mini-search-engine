# crawler.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import deque
from models import db, CrawledData  # Import db and model from models.py

visited = set()
index_data = {}


def crawl(seed_url, max_pages=50):
    queue = deque([seed_url])
    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        try:
            response = requests.get(url, timeout=3)
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            title = soup.title.string if soup.title else url

            # Check if the URL already exists in the database
            existing_entry = CrawledData.query.filter_by(url=url).first()
            if not existing_entry:
                # Save crawled data to the database if URL doesn't exist
                crawled_data = CrawledData(url=url, title=title, text=text)
                db.session.add(crawled_data)
                db.session.commit()

                # Add crawled data to the index_data
                index_data[url] = {"title": title, "text": text}
                visited.add(url)
                print(f"Crawled and saved URL: {url}")
            else:
                print(f"URL already exists: {url}")

            # Find and queue up all the links from the page
            for a in soup.find_all("a", href=True):
                full_url = urljoin(url, a["href"])
                if full_url.startswith("http"):
                    queue.append(full_url)

        except requests.exceptions.RequestException as e:
            print(f"Error crawling {url}: {e}")
            continue
