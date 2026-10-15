from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    messages_from_dict,
    messages_to_dict,
)

import discord
import requests
from discord.utils import escape_mentions, remove_markdown
import json
from models import load_model
from utils import (
    remove_mention,
    convert_id_to_name,
    convert_name_to_id,
    add_author,
    remove_author,
)
import hydra
from omegaconf import DictConfig
from time import sleep, time
import asyncio
import docx
import json
import requests
import xmltodict
import tempfile
from pathlib import Path
from reference_processing import batches, decode_references, article_index, format_references


def GetMedlinePage(start, end):
    if start == end:
        return start

    start_with_zero = (len(end) - len(start)) * "0" + start
    same_cnt = 0
    for e, s in zip(end, start_with_zero):
        if e == s:
            same_cnt += 1
        else:
            break
    medline_page = f":{start}-{end[same_cnt:]}"
    return medline_page


class LLMBot(discord.Client):
    def __init__(self, config, intents):
        super().__init__(heartbeat_timeout=60, intents=intents)
        self.config = config
        self.model = load_model(self.config["model"])

    async def on_ready(self):
        print("Logged on as {0}!".format(self.user))
        await self.change_presence(
            status=discord.Status.online, activity=discord.Game("대기중")
        )

    async def on_message(self, message):
        # Do not respond to ourselves
        if message.author == self.user:
            return
        # Do not respond to other system messages
        if message.content.startswith("***"):
            return
        # Only respond to the message if it is sent to the bot by mentioning
        if self.user.mentioned_in(message):
            # Check if the maximum number of turns has been reached
            thread = await message.create_thread(name="reply", auto_archive_duration=60)
            await thread.send("waiting for file to download...")
            if not message.attachments:
                await thread.send("Attach a DOCX file containing references.")
                return
            attachment = message.attachments[0]
            if not attachment.filename.lower().endswith(".docx"):
                await thread.send("Please attach a DOCX file.")
                return
            with tempfile.TemporaryDirectory(prefix="infolumi-input-") as directory:
                path = Path(directory) / "input.docx"
                await attachment.save(str(path))
                await self.test(str(path), thread)

    async def test(self, fname, thread):
        # check the total time
        start_time = time()
        channel = self.get_channel(self.config["discord"]["channel_id"])
        system_message_prompt = SystemMessagePromptTemplate.from_template(
            self.config["template"]["system"]
        )
        parse_template = self.config["template"]["parse"]
        human_message_prompt = HumanMessagePromptTemplate.from_template(parse_template)
        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )
        ref_list = []
        ref_size = 5
        templ = docx.Document(fname)
        for x, paragraph in enumerate(templ.paragraphs):
            ref_list.append(paragraph.text)
        chunks = batches(ref_list, ref_size)
        tasks = []
        for i, sub_list in enumerate(chunks):
            temp = chat_prompt.format_prompt(references="\n".join(sub_list)).to_messages()
            tasks.append(self.parse_reference(temp, channel, i, len(chunks), thread))
        responses = await asyncio.gather(*tasks)
        results_list = [reference
                        for response, chunk in zip(responses, chunks)
                        for reference in decode_references(response, len(chunk))]
        uid_list = []
        for i, reference in enumerate(results_list):
            if reference is None:
                uid_list.append(None)
            else:
                uid_list.append(self.search_pubmed(reference))
                await asyncio.sleep(0.3)

        uid_without_none = [x for x in uid_list if x is not None]
        uid_to_article = self.fetch_pubmed(uid_without_none)
        results = self.revise_reference(uid_list, uid_to_article)

        output_format = self.config.get("output_format", "docx")
        if output_format not in {"docx", "txt"}:
            raise ValueError("output_format must be docx or txt")
        with tempfile.TemporaryDirectory(prefix="infolumi-output-") as directory:
            output = Path(directory) / ("references." + output_format)
            if output_format == "docx":
                document = docx.Document()
                for reference in results:
                    document.add_paragraph(reference)
                document.save(output)
            else:
                output.write_text("\n".join(results), encoding="utf-8")
            with discord.File(str(output)) as attachment:
                await thread.send(f"Done in {(time()-start_time):.2} seconds", file=attachment)

    async def parse_reference(self, messages, channel, index, max_turn, thread):
        results = await self.model.agenerate(messages)
        await thread.send(f"parsing references {index+1}/{max_turn} done")
        return results

    def search_pubmed(self, reference):
        params = {
            "method": "auto",
            "authors": (reference.get("authors") or [""])[0],
            "title": reference.get("title", ""),
            "pdat": str(reference.get("year", "")),
            "volume": reference.get("volume", ""),
            "journal": reference.get("journal", ""),
        }
        try:
            res = requests.get(
                "https://pubmed.ncbi.nlm.nih.gov/api/citmatch/?", params=params, timeout=30
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
        except:
            return None

        return None

    def fetch_pubmed(self, uid_list):
        if not uid_list:
            return {}
        data = {"db": "pubmed", "id": ",".join(str(uid) for uid in uid_list), "retmode": "xml"}
        response = requests.post(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi", data=data, timeout=30)
        response.raise_for_status()
        return article_index(xmltodict.parse(response.text))

    def revise_reference(self, uid_list, uid_to_article):
        return format_references(uid_list, uid_to_article)


@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(config: DictConfig) -> None:
    intents = discord.Intents.all()
    client = LLMBot(config=config, intents=intents)
    client.run(config["discord"]["token"])


if __name__ == "__main__":
    main()
