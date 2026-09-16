import json, re
def canon(t):
    t = re.sub(r"\s*\([^)]*\)\s*", " ", t.lower().strip())
    t = re.sub(r"[^a-z0-9 \-]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return re.sub(r"[\s\-]+", "", t)

with open("data/processed/corpus.json", encoding="utf-8") as f:
    corpus = json.load(f)
a = next((x for x in corpus if x["pmid"] == "18801947"), None)
print("Présent dans le corpus :", a is not None)
if a:
    t = canon(a["titre"] + " " + a["resume"])
    print("indatraline :", "indatraline" in t)
    print("fluoxetine  :", "fluoxetine" in t)