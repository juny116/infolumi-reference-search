"""Index PubMed article metadata by PMID."""


def article_index(document):
    """Index PubMed XML dictionaries by PMID, never by server response order."""
    container = document.get("PubmedArticleSet") or {}
    entries = container.get("PubmedArticle", [])
    if isinstance(entries, dict):
        entries = [entries]
    result = {}
    for entry in entries or []:
        citation = entry.get("MedlineCitation") or {}
        pmid = citation.get("PMID")
        if isinstance(pmid, dict):
            pmid = pmid.get("#text")
        if pmid is not None and citation.get("Article"):
            result[str(pmid)] = citation["Article"]
    return result
