import unittest

from infolumi.article_metadata import article_index
from infolumi.citation_formatting import format_references
from infolumi.reference_parsing import batches, decode_references


class ReferenceProcessingTests(unittest.TestCase):
    def test_batches_cover_every_reference(self):
        self.assertEqual([len(x) for x in batches(list(range(12)))], [5, 5, 2])
        self.assertEqual(batches([]), [])
        self.assertEqual([len(x) for x in batches(list(range(10)))], [5, 5])

    def test_bad_model_output_preserves_positions(self):
        self.assertEqual(decode_references("not json", 2), [None, None])
        self.assertEqual(decode_references('{"title":"wrong shape"}', 1), [None])
        self.assertEqual(
            decode_references('[{"title":"A"}]', 2), [{"title": "A"}, None]
        )
        self.assertEqual(decode_references("```json\n[{}, {}]\n```", 1), [{}])

    def test_index_does_not_assume_response_order(self):
        second = {
            "MedlineCitation": {
                "PMID": {"#text": "2"},
                "Article": {"ArticleTitle": "B"},
            }
        }
        first = {"MedlineCitation": {"PMID": "1", "Article": {"ArticleTitle": "A"}}}
        self.assertEqual(
            article_index({"PubmedArticleSet": {"PubmedArticle": [second, first]}})[
                "1"
            ]["ArticleTitle"],
            "A",
        )
        self.assertEqual(
            article_index({"PubmedArticleSet": {"PubmedArticle": first}})["1"][
                "ArticleTitle"
            ],
            "A",
        )
        self.assertEqual(article_index({"PubmedArticleSet": None}), {})

    def test_missing_reference_and_single_author(self):
        data = {
            "1": {
                "ArticleTitle": "Example",
                "AuthorList": {"Author": {"LastName": "Doe", "Initials": "J"}},
                "Journal": {
                    "ISOAbbreviation": "J Test",
                    "JournalIssue": {"PubDate": {"Year": "2000"}},
                },
            }
        }
        actual = format_references([None, "1", "missing"], data)
        self.assertEqual(actual[0], "1. Not Found")
        self.assertIn("Doe J.", actual[1])
        self.assertEqual(actual[2], "3. Not Found")

    def test_group_author_and_medline_pages(self):
        data = {
            "7": {
                "ArticleTitle": "Example",
                "AuthorList": {"Author": {"CollectiveName": "Test Group"}},
                "Journal": {"Title": "Example Journal"},
                "Pagination": {"MedlinePgn": "10-12"},
            }
        }
        self.assertIn("Test Group.", format_references(["7"], data)[0])
        self.assertTrue(format_references(["7"], data)[0].endswith(":10-12."))


if __name__ == "__main__":
    unittest.main()
