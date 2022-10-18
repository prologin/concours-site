"""
Send messages to the Discord webhook configured with PROLOGIN_NEW_SCHOOL_NOTIFY
"""

import requests
import logging

from django.conf import settings
from typing import Any


MISSING: Any = object()


def send_message(
    *,
    title: str = None,
    url: str = None,
    description: str = None,
    color: int = 0x35479A,
    embed_dict: dict = None,
    content: str = None,
):
    """
    Send a message to the configured Discord webhook.
    Will only work if a webhook link is configured with PROLOGIN_DISCORD_WEBHOOK.
    
    See this link for details on how Discord embeds work:
    https://discord.com/developers/docs/resources/channel#embed-object

    Arguments
    ---------
    title: str
        Title of the embed
    url: str
        Makes the title a hyperlink with the given URL
    description: str
        Description of the embed (max 1024 characters)
    color: int
        24-bit RGB color code for the embed. Defaults to the Prologin theme.
    embed_dict: dict
        Pass a complete embed dictionnary to use all features, see link above
    content: str
        Content of the message above the embed (max 2000 characters)
    """
    webhook_url = settings.PROLOGIN_DISCORD_WEBHOOK
    if not webhook_url:
        return
    embed = {
        "title": title,
        "url": url,
        "description": description,
        "color": color,
    }
    if embed_dict:
        embed.update(embed_dict)
    data = {
        "username": "Site Prologin",
        "avatar_url": "https://gitlab.com/uploads/-/system/project/avatar/38229465/site.png",
        "content": content,
        "embeds": [embed],
    }
    try:
        requests.post(webhook_url, params={"wait": True}, json=data)
    except Exception:
        logging.exception("Could not send Discord notification", exc_info=True)
