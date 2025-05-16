from flask import Flask, request, render_template, jsonify
from models import db, CrawledData  # Import db and CrawledData from models.py
from crawler import crawl, index_data
from ranker import SearchRanker  # Import SearchRanker from ranker.py

app = Flask(__name__)

# Setup the app's database URI (assuming SQLite)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///crawled_data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database
db.init_app(app)

# Ensure we are inside the app context when querying the database
with app.app_context():
    # Create tables if they don't exist
    db.create_all()

    # Only crawl if the database is empty
    if not CrawledData.query.first():  # Check if the table is empty
        crawl("https://example.com", max_pages=20)  # Crawl the data

    # Fetch all crawled data from the database
    crawled_data = CrawledData.query.all()

    # Pass crawled data to SearchRanker
    ranker = SearchRanker(crawled_data)


@app.route("/")
def home():
    return render_template("search.html")


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    page_num = int(request.args.get("page", 1))  # Get the page number
    results_per_page = 10  # Number of results per page

    if not query:
        return render_template("search.html", results=[], page_num=page_num)

    ranked = ranker.search(query, page_num=page_num, results_per_page=results_per_page)
    final = [(url, title, snippet, summary) for url, title, snippet, summary in ranked]

    # Calculate total results from the search function
    total_results = len(ranked)  # Total number of results returned by the search
    total_pages = (total_results // results_per_page) + (
        1 if total_results % results_per_page > 0 else 0
    )

    return render_template(
        "search.html",
        results=final,
        query=query,
        page_num=page_num,
        total_pages=total_pages,
    )


@app.route("/autocomplete")
def autocomplete():
    term = request.args.get("term", "").lower()
    suggestions = sorted([w for w in ranker.all_words if w.startswith(term)])[:10]
    return jsonify(suggestions)


if __name__ == "__main__":
    app.run(debug=True)
