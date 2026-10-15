"""PubMed citation matching and PMID metadata retrieval."""

import requests
import xmltodict

from .article_metadata import article_index


class PubMedClient:
    def __init__(self, session=None):
        self.session = session or requests

    def search(self, reference):
        params = {
            "method": "auto",
            "authors": (reference.get("authors") or [""])[0],
            "title": reference.get("title", ""),
            "pdat": str(reference.get("year", "")),
            "volume": reference.get("volume", ""),
            "journal": reference.get("journal", ""),
        }
        try:
            res = self.session.get(
                "https://pubmed.ncbi.nlm.nih.gov/api/citmatch/?",
                params=params,
                timeout=30,
            )
            result = res.json().get("result")
            uids = result.get("uids")
            if not uids:
                return None
            # return the first uid
            for uid in uids:
                for k, v in uid.items():
                    if k == "pubmed":
                        return v
        except (requests.RequestException, ValueError, AttributeError, TypeError):
            return None

        return None

    def fetch(self, uid_list):
        if not uid_list:
            return {}
        data = {
            "db": "pubmed",
            "id": ",".join(str(uid) for uid in uid_list),
            "retmode": "xml",
        }
        response = self.session.post(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            data=data,
            timeout=30,
        )
        response.raise_for_status()
        return article_index(xmltodict.parse(response.text))
