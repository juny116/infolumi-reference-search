import re


def remove_mention(text):
    text = re.sub(r"<@(everyone|here|[!&]?[0-9]{17,20})>", "", text).strip()
    text = re.sub(r"@(everyone|here)", "", text).strip()
    return text


def convert_name_to_id(name_to_id, text):
    def repl(mention):
        name = mention.group(1)
        if name == "everyone" or name == "here":
            return f"@{name}"
        else:
            return f"<@{name_to_id[name]}>" if name in name_to_id else mention.group(0)

    text = re.sub(r"<@([a-zA-Z0-9\uac00-\ud7a3]*)>", repl, text, re.MULTILINE)

    return text


def convert_id_to_name(id_to_name, text):
    def repl(mention):
        id = mention.group(1)
        if id == "everyone" or id == "here":
            return f"@{id}"
        else:
            key = id.lstrip("!&")
            return f"<@{id_to_name[key]}>" if key in id_to_name else mention.group(0)

    text = re.sub(r"<@([!&]?[0-9]{17,20})>", repl, text, re.MULTILINE)

    return text


def add_author(name, text):
    if not text.startswith(name + ":"):
        return f"{name}: {text}"
    else:
        return text


def remove_author(name, text):
    text = text.strip()
    if text.startswith(name + ":"):
        return text[len(name) + 1 :].strip()
    else:
        return text


def messages_to_prompt(messages):
    prompt = ""
    for message in messages:
        prompt += message.content + "\n"

    return prompt
