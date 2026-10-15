"""Turn reference lines into structured citations with a language model."""


class ModelReferenceParser:
    def __init__(self, model, template):
        from langchain.prompts.chat import (
            ChatPromptTemplate,
            HumanMessagePromptTemplate,
            SystemMessagePromptTemplate,
        )

        self.model = model
        self.prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(template["system"]),
                HumanMessagePromptTemplate.from_template(template["parse"]),
            ]
        )

    async def parse(self, references):
        messages = self.prompt.format_prompt(
            references="\n".join(references)
        ).to_messages()
        return await self.model.agenerate(messages)
