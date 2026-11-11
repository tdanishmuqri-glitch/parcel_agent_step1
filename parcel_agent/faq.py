"""RAG: let the agent look up answers in the company FAQ before replying.

How it works:
1. Each FAQ entry is turned into an "embedding" - a list of numbers that
   represents its MEANING. Similar meanings get similar numbers.
2. The customer's question is turned into an embedding the same way.
3. We compare the question with every FAQ entry and return the closest ones.
"""
import math

from google import genai
from google.genai import types

# The company knowledge base. In a real company this could be hundreds of
# help-centre articles stored in a database.
FAQS = [
    {"question": "What items am I not allowed to send?",
     "answer": "Prohibited items include weapons, explosives, flammable liquids, illegal drugs, "
               "cash, and live animals. Power banks and loose lithium batteries cannot be sent by air."},
    {"question": "How do I reschedule my delivery?",
     "answer": "Reply to your delivery SMS or use the tracking page to choose a new date, up to 5 days ahead. "
               "Rescheduling is free."},
    {"question": "Why is my parcel held at customs?",
     "answer": "International parcels are checked by customs. Holds usually take 1-3 working days. "
               "You may be asked for an invoice or to pay import duty and tax before release."},
    {"question": "What happens if I am not home during delivery?",
     "answer": "The courier will try again the next working day. After 2 failed attempts the parcel "
               "is kept at the nearest service point for 7 days, then returned to the sender."},
    {"question": "How long does delivery take?",
     "answer": "Within Peninsular Malaysia: 1-3 working days. To Sabah and Sarawak: 3-5 working days. "
               "International: 3-10 working days depending on the country."},
    {"question": "How do I report a damaged parcel?",
     "answer": "Report it within 48 hours of delivery with photos of the parcel and item. "
               "Keep the packaging until the claim is resolved."},
    {"question": "My parcel is lost. What can I do?",
     "answer": "If tracking has not updated for 7 working days, we open a lost parcel investigation. "
               "Investigations take up to 10 working days. Compensation follows the sender's coverage."},
    {"question": "Can I change my delivery address?",
     "answer": "You can change the address once, before the parcel is out for delivery, "
               "from the tracking page. A small fee may apply for a different city."},
    {"question": "What are your customer service hours?",
     "answer": "Customer service is open Monday to Saturday, 8am to 8pm, excluding public holidays."},
    {"question": "Do you deliver on weekends?",
     "answer": "Yes, we deliver on Saturdays in major cities. There is no delivery on Sundays or public holidays."},
]

EMBEDDING_MODEL = "gemini-embedding-2"
_faq_vectors = None   # filled the first time someone searches, then reused


def _embed(texts):
    """Turn a list of texts into a list of embeddings (one list of numbers each)."""
    client = genai.Client()  # uses GOOGLE_API_KEY from .env
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[types.Content(parts=[types.Part.from_text(text=t)]) for t in texts],
        config=types.EmbedContentConfig(output_dimensionality=768),
    )
    return [e.values for e in result.embeddings]


def _similarity(a, b):
    """Cosine similarity: close to 1.0 = same meaning, close to 0 = unrelated."""
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def search_faq(customer_question: str) -> dict:
    """Search the company FAQ for answers to a customer's policy question.

    Use this for questions about rules and services, e.g. prohibited items,
    rescheduling, customs, delivery times, damaged or lost parcels.

    Args:
        customer_question: The customer's question in their own words.
    """
    global _faq_vectors
    if _faq_vectors is None:
        _faq_vectors = _embed([f"title: {f['question']} | text: {f['answer']}" for f in FAQS])

    question_vector = _embed([f"task: question answering | query: {customer_question}"])[0]
    scored = [(_similarity(question_vector, vec), faq) for vec, faq in zip(_faq_vectors, FAQS)]
    scored.sort(key=lambda pair: pair[0], reverse=True)

    top_two = [{"score": round(score, 2), **faq} for score, faq in scored[:2]]
    return {"results": top_two}


# Test the search on its own:  python -m parcel_agent.faq "can I send a power bank?"
if __name__ == "__main__":
    import sys
    from pathlib import Path
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent / ".env")
    for r in search_faq(" ".join(sys.argv[1:]) or "can I send a power bank?")["results"]:
        print(r["score"], "-", r["question"])
