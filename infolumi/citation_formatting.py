"""Format article metadata in original reference order."""


def _text(value):
    if isinstance(value, dict):
        return str(value.get("#text", ""))
    return "" if value is None else str(value)


def format_references(uids, articles):
    """Format available metadata while preserving missing references in place."""
    formatted = []
    for position, uid in enumerate(uids, 1):
        article = articles.get(str(uid)) if uid is not None else None
        if not article:
            formatted.append(f"{position}. Not Found")
            continue
        authors = (article.get("AuthorList") or {}).get("Author", [])
        if isinstance(authors, dict):
            authors = [authors]
        abbreviated = len(authors) > 6
        authors = authors[:3] if abbreviated else authors
        author_text = ", ".join(
            _text(a.get("CollectiveName"))
            or " ".join(
                filter(None, (_text(a.get("LastName")), _text(a.get("Initials"))))
            )
            for a in authors
        )
        if abbreviated:
            author_text += ", et al"
        journal = article.get("Journal") or {}
        issue = journal.get("JournalIssue") or {}
        date = issue.get("PubDate") or {}
        citation = " ".join(
            filter(
                None,
                (
                    author_text + "." if author_text else "",
                    _text(article.get("ArticleTitle")),
                    _text(journal.get("ISOAbbreviation") or journal.get("Title")) + ".",
                    _text(date.get("Year") or date.get("MedlineDate")),
                ),
            )
        )
        if issue.get("Volume"):
            citation += ";" + _text(issue["Volume"])
        if issue.get("Issue"):
            citation += "(" + _text(issue["Issue"]) + ")"
        pages = article.get("Pagination") or {}
        page = pages.get("MedlinePgn") or pages.get("StartPage")
        if page:
            citation += ":" + _text(page)
            if pages.get("EndPage") and pages["EndPage"] != page:
                citation += "-" + _text(pages["EndPage"])
        formatted.append(f"{position}. {citation.rstrip('.')}.")
    return formatted
