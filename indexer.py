# indexer.py
from collections import defaultdict
import re


def build_inverted_index(data):
    index = defaultdict(set)
    for url, content in data.items():
        words = re.findall(r"\w+", content["text"].lower())
        for word in words:
            index[word].add(url)
    return index
