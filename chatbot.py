from sentence_transformers import SentenceTransformer, util
from fuzzywuzzy import fuzz
from groq import Groq
import torch
import json
import os

# Load Groq client safely
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def groq_chat(messages, model="llama-3.1-8b-instant"):
    """Safely call Groq API and always return plain text."""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages
        )

        if resp and resp.choices:
            return resp.choices[0].message.content.strip()


        return "⚠️ No response from AI."

    except Exception as e:
        return f"⚠️ GPT Error: {str(e)}"


class FAQChatbot:
    def __init__(self, faqs, threshold=0.45):
        self.faqs = faqs
        self.threshold = threshold

        self.questions = [f["question"] for f in faqs]
        self.answers = [f["answer"] for f in faqs]

        # SBERT
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.embeddings = self.model.encode(self.questions, convert_to_tensor=True)

    def faq_answer(self, query):
        query_emb = self.model.encode(query, convert_to_tensor=True)
        scores = util.cos_sim(query_emb, self.embeddings)[0]

        best_idx = int(torch.argmax(scores))
        best_score = float(scores[best_idx])

        if best_score >= self.threshold:
            return self.answers[best_idx], best_score

        # Fallback fuzzy search
        best_fuzzy = 0
        best_fuzzy_ans = None

        for q, a in zip(self.questions, self.answers):
            score = fuzz.token_set_ratio(query.lower(), q.lower())
            if score > best_fuzzy:
                best_fuzzy = score
                best_fuzzy_ans = a

        if best_fuzzy >= 70:
            return best_fuzzy_ans, best_fuzzy / 100

        return None, best_score

    def gpt_answer(self, query):
        messages = [
            {"role": "system",
             "content": "Answer concisely and helpfully about the college."},
            {"role": "user", "content": query}
        ]
        return groq_chat(messages)

    def answer(self, query):
        faq_ans, score = self.faq_answer(query)

        if faq_ans:
            return faq_ans, "FAQ", score

        gpt_ans = self.gpt_answer(query)
        return gpt_ans, "GPT", 0.0


def load_faqs(path="faqs.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
