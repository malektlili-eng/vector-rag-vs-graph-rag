# dashboard.py
# Tableau de bord comparatif — Vector RAG contre Graph RAG.
# Lancement : streamlit run dashboard.py

import json
from collections import defaultdict

import streamlit as st

EVALUATION = "data/processed/evaluation_ragas.json"
CORPUS = "data/processed/corpus.json"

st.set_page_config(page_title="Vector RAG vs Graph RAG",
                   layout="wide", initial_sidebar_state="expanded")


@st.cache_data
def charger():
    with open(EVALUATION, encoding="utf-8") as fichier:
        reponses = json.load(fichier)
    with open(CORPUS, encoding="utf-8") as fichier:
        corpus = {a["pmid"]: a for a in json.load(fichier)}
    par_question = defaultdict(dict)
    for r in reponses:
        par_question[r["id"]][r["pipeline"]] = r
    return reponses, corpus, par_question


reponses, corpus, par_question = charger()

# ---------- Barre latérale
st.sidebar.title("Vector RAG vs Graph RAG")
st.sidebar.caption("Inférence multi-hop sur corpus biomédical")

vue = st.sidebar.radio("Vue", ["Comparaison par question",
                               "Résultats d'ensemble"])

st.sidebar.divider()
st.sidebar.caption(
    "Résultats précalculés. La génération requiert un GPU et a été "
    "exécutée sur Google Colab ; l'interface restitue ces résultats."
)


def badge(r):
    if r["correct"]:
        return "✅ correct"
    if r["abstention"]:
        return "⚪ abstention"
    return "❌ incorrect"


# ---------- Vue 1 : question par question
if vue == "Comparaison par question":
    identifiants = sorted(par_question,
                          key=lambda x: (x[:2] != "MH", x))
    libelles = {
        i: f"{i} — {par_question[i]['graphe']['type']} — "
           f"{par_question[i]['graphe']['question'][:52]}…"
        for i in identifiants
    }
    choisi = st.sidebar.selectbox("Question", identifiants,
                                  format_func=lambda i: libelles[i])

    paire = par_question[choisi]
    v, g = paire["vectoriel"], paire["graphe"]

    st.header(v["question"])
    st.caption(f"{choisi} · {v['type']} · "
               f"réponse attendue : {', '.join(v['reponses_acceptables'])}")

    gauche, droite = st.columns(2)

    for colonne, r, titre in ((gauche, v, "Pipeline A — vectoriel"),
                              (droite, g, "Pipeline B — graphe")):
        with colonne:
            st.subheader(titre)
            st.markdown(f"**{badge(r)}**")
            st.info(r["reponse"])

            a, b, c = st.columns(3)
            a.metric("Fidélité", f"{r['fidelite']:.2f}"
                     if r["fidelite"] is not None else "—")
            b.metric("Pertinence", f"{r['pertinence']:.2f}"
                     if r["pertinence"] is not None else "—")
            c.metric("Latence", f"{r['latence']:.1f} s")

            attendus = set(r["pmids_attendus"])
            fournis = r["pmids_fournis"]
            trouves = attendus & set(fournis)
            rappel = len(trouves) / len(attendus) if attendus else 0
            st.caption(f"Rappel : {rappel:.2f} "
                       f"({len(trouves)}/{len(attendus)} documents attendus)")

            st.markdown("**Documents récupérés**")
            if not fournis:
                st.warning("Aucun document récupéré.")
            for i, pmid in enumerate(fournis, 1):
                marque = "🎯" if pmid in attendus else "　"
                titre_doc = corpus.get(pmid, {}).get("titre", "(absent)")
                with st.expander(f"{marque} {i}. PMID {pmid} — {titre_doc[:58]}"):
                    st.write(corpus.get(pmid, {}).get("resume", ""))

    manques = set(v["pmids_attendus"]) - set(v["pmids_fournis"]) \
              - set(g["pmids_fournis"])
    if manques:
        st.divider()
        st.caption("Documents attendus qu'aucun des deux pipelines n'a "
                   f"récupérés : {', '.join(sorted(manques))}")

# ---------- Vue 2 : agrégats
else:
    st.header("Résultats d'ensemble")
    st.caption(f"{len(par_question)} questions · "
               f"{sum(1 for i in par_question if i.startswith('MH'))} multi-hop, "
               f"{sum(1 for i in par_question if i.startswith('SH'))} single-hop")

    def agreger(sous):
        return {
            "Exactitude": sum(r["correct"] for r in sous) / len(sous),
            "Abstention": sum(r["abstention"] for r in sous) / len(sous),
            "Fidélité": sum(r["fidelite"] for r in sous
                            if r["fidelite"] is not None) / len(sous),
            "Pertinence": sum(r["pertinence"] for r in sous
                              if r["pertinence"] is not None) / len(sous),
        }

    lignes = {}
    for pipeline in ("vectoriel", "graphe"):
        lignes[pipeline] = agreger([r for r in reponses
                                    if r["pipeline"] == pipeline])
    st.subheader("Toutes questions")
    st.table(lignes)

    st.subheader("Par catégorie de question")
    for genre in ("single-hop", "pont", "intersection"):
        sous_lignes = {}
        for pipeline in ("vectoriel", "graphe"):
            sous = [r for r in reponses
                    if r["pipeline"] == pipeline and r["type"] == genre]
            if sous:
                sous_lignes[pipeline] = agreger(sous)
        if sous_lignes:
            n = len([r for r in reponses
                     if r["pipeline"] == "graphe" and r["type"] == genre])
            st.markdown(f"**{genre}** — {n} questions")
            st.table(sous_lignes)

    st.divider()
    st.subheader("Lecture des métriques")
    st.markdown(
        "- **Exactitude** — la réponse contient l'une des formulations "
        "attendues. Mesure déterministe, sans juge.\n"
        "- **Abstention** — le système déclare l'information absente des "
        "documents fournis.\n"
        "- **Fidélité** — la réponse est soutenue par les documents. "
        "Une abstention justifiée y est notée au maximum : prise isolément, "
        "cette métrique récompense le silence.\n"
        "- **Pertinence** — la réponse traite la question posée. "
        "Une abstention y est pénalisée."
    )