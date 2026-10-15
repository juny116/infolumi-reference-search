"""Discord attachment handling for reference processing."""

import asyncio
import tempfile
from pathlib import Path
from time import monotonic

import discord

from .chat_model import load_model
from .documents import write_references
from .model_parser import ModelReferenceParser
from .pipeline import ReferencePipeline
from .pubmed_client import PubMedClient


class ReferenceSearchBot(discord.Client):
    def __init__(self, config, intents, pipeline=None):
        super().__init__(heartbeat_timeout=60, intents=intents)
        self.config = config
        self.pipeline = pipeline or ReferencePipeline(
            ModelReferenceParser(load_model(config["model"]), config["template"]),
            PubMedClient(),
        )

    async def on_ready(self):
        print(f"Logged on as {self.user}!")
        await self.change_presence(
            status=discord.Status.online, activity=discord.Game("대기중")
        )

    async def on_message(self, message):
        if message.author == self.user or message.content.startswith("***"):
            return
        if not self.user.mentioned_in(message):
            return
        thread = await message.create_thread(name="reply", auto_archive_duration=60)
        if not message.attachments:
            await thread.send("Attach a DOCX file containing references.")
            return
        attachment = message.attachments[0]
        if not attachment.filename.lower().endswith(".docx"):
            await thread.send("Please attach a DOCX file.")
            return
        output_format = self.config.get("output_format", "docx")
        if output_format not in {"docx", "txt"}:
            raise ValueError("output_format must be docx or txt")
        started = monotonic()

        async def progress(index, total):
            await thread.send(f"parsing references {index}/{total} done")

        with tempfile.TemporaryDirectory(prefix="infolumi-") as directory:
            source = Path(directory) / "input.docx"
            output = Path(directory) / ("references." + output_format)
            await attachment.save(str(source))
            references = await self.pipeline.process(source, progress)
            await asyncio.to_thread(write_references, references, output)
            with discord.File(str(output)) as result:
                await thread.send(
                    f"Done in {monotonic() - started:.2f} seconds", file=result
                )
