from src.metrics import build_metrics
from src.flagging import flag_rows
from src.notes import load_notes
from src.retrieval import NoteRetriever, QUERY_PREFIX

notes = load_notes("data/context_notes.csv")
retriever = NoteRetriever(notes)
flags = flag_rows(build_metrics("data/shipment_records.csv"))


def count_tokens(text):
    return len(retriever.model.tokenizer.encode(text))


doc_tokens = sum(count_tokens(a + ". " + n) for a, n in zip(notes["applies_to"], notes["note"]))
query_tokens = sum(
    count_tokens(QUERY_PREFIX + f"Why did freight cost rise on the {r['route']} route "
                 f"in the week of {r['week_of']:%d %B %Y}?")
    for _, r in flags.iterrows())

print("LLM calls:            0")
print("LLM input tokens:     0")
print("LLM output tokens:    0")
print(f"Embedding tokens (notes, embedded once): {doc_tokens}")
print(f"Embedding tokens (queries, {len(flags)} flagged rows): {query_tokens}")
print("Cost: $0 (local open-source model BAAI/bge-small-en-v1.5, no API)")