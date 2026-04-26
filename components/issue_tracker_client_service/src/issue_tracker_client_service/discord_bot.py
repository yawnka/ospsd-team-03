"""Discord bot entrypoint for AI issue tracker commands."""

import logging
import os

import discord
from chat_client_api import get_client as get_chat_client
from issue_tracker_client_impl.client import DefaultIssueTrackerClient

from issue_tracker_client_service.ai_router import run_ai_chat
from issue_tracker_client_service.ai_schemas import AIChatIn

logger = logging.getLogger(__name__)


class IssueTrackerBot(discord.Client):
    """Discord bot that sends mentions to the AI issue tracker."""

    async def on_ready(self) -> None:
        """Handle bot startup and confirm successful login."""
        logger.info("Logged in as %s", self.user)

    async def on_message(self, message: discord.Message) -> None:
        """Handle incoming Discord messages and forward bot mentions to the AI."""
        if message.author.bot:
            return

        if self.user is None or self.user not in message.mentions:
            return

        prompt = message.content.replace(f"<@{self.user.id}>", "").strip()
        prompt = prompt.replace(f"<@!{self.user.id}>", "").strip()

        if not prompt:
            get_chat_client().send_message(
                channel_id=str(message.channel.id),
                text="Ask me something like: `@issuetrackerbot list all boards`",
            )
            return

        try:
            issue_tracker_client = DefaultIssueTrackerClient(
                api_key=os.environ["TRELLO_API_KEY"],
                token=os.environ["TRELLO_API_TOKEN"],
            )

            response = run_ai_chat(
                payload=AIChatIn(message=prompt),
                issue_tracker_client=issue_tracker_client,
            )

            get_chat_client().send_message(
                channel_id=str(message.channel.id),
                text=f"AI response:\n{response.reply}"
            )

        except Exception:
            logger.exception("Discord AI command failed")
            get_chat_client().send_message(
                channel_id=str(message.channel.id),
                text="Sorry, I couldn't complete that issue tracker request.",
            )



intents = discord.Intents.default()
intents.message_content = True

bot = IssueTrackerBot(intents=intents)
bot.run(os.environ["DISCORD_BOT_TOKEN"])
