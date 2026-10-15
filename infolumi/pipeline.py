"""Parse reference batches, resolve PubMed records and format citations."""

import asyncio

from .citation_formatting import format_references
from .documents import read_references
from .reference_parsing import batches, decode_references


class ReferencePipeline:
    def __init__(self, parser, pubmed, *, batch_size=5, search_delay=0.3):
        self.parser = parser
        self.pubmed = pubmed
        self.batch_size = batch_size
        self.search_delay = search_delay

    async def process(self, path, progress=None):
        references = await asyncio.to_thread(read_references, path)
        chunks = batches(references, self.batch_size)

        async def parse_chunk(index, chunk):
            response = await self.parser.parse(chunk)
            if progress:
                await progress(index + 1, len(chunks))
            return decode_references(response, len(chunk))

        parsed = await asyncio.gather(
            *(parse_chunk(i, chunk) for i, chunk in enumerate(chunks))
        )
        ids = []
        for reference in (ref for chunk in parsed for ref in chunk):
            if reference is None:
                ids.append(None)
            else:
                ids.append(await asyncio.to_thread(self.pubmed.search, reference))
                await asyncio.sleep(self.search_delay)
        articles = await asyncio.to_thread(
            self.pubmed.fetch, [uid for uid in ids if uid is not None]
        )
        return format_references(ids, articles)
