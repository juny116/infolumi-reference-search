"""Pure reference-processing helpers; no network calls or private configuration."""
import json


def batches(items, size=5):
    if size <= 0:
        raise ValueError('size must be positive')
    return [items[i:i + size] for i in range(0, len(items), size)]


def decode_references(response, expected_count):
    """Keep positional alignment when a model returns invalid or partial JSON."""
    text = response.strip()
    if text.startswith('```') and text.endswith('```'):
        text = '\n'.join(text.splitlines()[1:-1])
    try:
        items = json.loads(text)
    except (ValueError, TypeError):
        items = []
    if not isinstance(items, list):
        items = []
    items = [x if isinstance(x, dict) else None for x in items[:expected_count]]
    return items + [None] * (expected_count - len(items))


def article_index(document):
    """Index PubMed XML dictionaries by PMID, never by server response order."""
    container = document.get('PubmedArticleSet') or {}
    entries = container.get('PubmedArticle', [])
    if isinstance(entries, dict):
        entries = [entries]
    result = {}
    for entry in entries or []:
        citation = entry.get('MedlineCitation') or {}
        pmid = citation.get('PMID')
        if isinstance(pmid, dict):
            pmid = pmid.get('#text')
        if pmid is not None and citation.get('Article'):
            result[str(pmid)] = citation['Article']
    return result


def _text(value):
    if isinstance(value, dict):
        return str(value.get('#text', ''))
    return '' if value is None else str(value)


def format_references(uids, articles):
    """Format available metadata while preserving missing references in place."""
    formatted = []
    for position, uid in enumerate(uids, 1):
        article = articles.get(str(uid)) if uid is not None else None
        if not article:
            formatted.append(f'{position}. Not Found')
            continue
        authors = (article.get('AuthorList') or {}).get('Author', [])
        if isinstance(authors, dict):
            authors = [authors]
        abbreviated = len(authors) > 6
        authors = authors[:3] if abbreviated else authors
        author_text = ', '.join(
            _text(a.get('CollectiveName')) or ' '.join(filter(None, (
                _text(a.get('LastName')), _text(a.get('Initials')))))
            for a in authors)
        if abbreviated:
            author_text += ', et al'
        journal = article.get('Journal') or {}
        issue = journal.get('JournalIssue') or {}
        date = issue.get('PubDate') or {}
        citation = ' '.join(filter(None, (
            author_text + '.' if author_text else '',
            _text(article.get('ArticleTitle')),
            _text(journal.get('ISOAbbreviation') or journal.get('Title')) + '.',
            _text(date.get('Year') or date.get('MedlineDate')))))
        if issue.get('Volume'):
            citation += ';' + _text(issue['Volume'])
        if issue.get('Issue'):
            citation += '(' + _text(issue['Issue']) + ')'
        pages = article.get('Pagination') or {}
        page = pages.get('MedlinePgn') or pages.get('StartPage')
        if page:
            citation += ':' + _text(page)
            if pages.get('EndPage') and pages['EndPage'] != page:
                citation += '-' + _text(pages['EndPage'])
        formatted.append(f'{position}. {citation.rstrip(".")}.')
    return formatted
