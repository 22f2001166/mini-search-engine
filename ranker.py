import re
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import T5ForConditionalGeneration, T5Tokenizer


class SearchRanker:
    def __init__(self, crawled_data):
        self.urls = []
        self.docs = []
        self.index_data = {}
        self.summary_cache = {}  # Cache for summaries

        # Process the crawled data
        for entry in crawled_data:
            self.urls.append(entry.url)
            self.docs.append(entry.text)
            self.index_data[entry.url] = {"title": entry.title, "text": entry.text}

        # Initialize TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.tfidf_matrix = self.vectorizer.fit_transform(self.docs)

        # Initialize T5 tokenizer and model
        self.tokenizer = T5Tokenizer.from_pretrained("t5-small")
        self.model = T5ForConditionalGeneration.from_pretrained("t5-small")

        # Set of all words for autocomplete suggestions
        self.all_words = set(word for doc in self.docs for word in doc.lower().split())

    def summarize_text(self, text):
        # Check if the summary is cached
        if text in self.summary_cache:
            return self.summary_cache[text]

        # Preprocess text and generate summary using T5
        input_text = "summarize: " + text
        inputs = self.tokenizer(
            input_text, return_tensors="pt", max_length=512, truncation=True
        )
        summary_ids = self.model.generate(
            inputs["input_ids"],
            max_length=150,
            min_length=40,
            length_penalty=2.0,
            num_beams=4,
            early_stopping=True,
        )
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)

        # Cache the summary
        self.summary_cache[text] = summary
        return summary

    def generate_snippet(self, text, query):
        text_lower = text.lower()
        query_words = query.lower().split()
        for word in query_words:
            idx = text_lower.find(word)
            if idx != -1:
                start = max(0, idx - 40)
                end = min(len(text), idx + 60)
                snippet = text[start:end]
                # Highlight all query words
                for q in query_words:
                    snippet = re.sub(
                        f"(?i)({re.escape(q)})", r"<mark>\1</mark>", snippet
                    )
                return snippet + "..."
        return text[:100] + "..."

    def summarize_text(self, text):
        # Preprocess text and generate summary using T5
        input_text = "summarize: " + text
        inputs = self.tokenizer(
            input_text, return_tensors="pt", max_length=512, truncation=True
        )
        summary_ids = self.model.generate(
            inputs["input_ids"],
            max_length=150,
            min_length=40,
            length_penalty=2.0,
            num_beams=4,
            early_stopping=True,
        )
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary

    def search(self, query, top_k=10, page_num=1, results_per_page=10):
        # Perform the search and get the ranked results
        query_vec = self.vectorizer.transform([query])
        scores = (self.tfidf_matrix @ query_vec.T).toarray()
        ranked_indices = scores.flatten().argsort()[::-1]

        # Pagination logic
        start_idx = (page_num - 1) * results_per_page
        end_idx = start_idx + results_per_page

        results = []
        for idx in ranked_indices[start_idx:end_idx]:
            if scores[idx] > 0:
                url = self.urls[idx]
                title = self.index_data[url]["title"]
                snippet = self.generate_snippet(self.index_data[url]["text"], query)
                summary = self.summarize_text(self.index_data[url]["text"])
                results.append((url, title, snippet, summary))

        return results
