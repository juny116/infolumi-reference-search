"""Run the Infolumi reference-search bot."""

import hydra


@hydra.main(version_base=None, config_path=None, config_name="config")
def main(config):
    import discord

    from .bot import ReferenceSearchBot

    client = ReferenceSearchBot(config, discord.Intents.all())
    client.run(config["discord"]["token"])


if __name__ == "__main__":
    main()
