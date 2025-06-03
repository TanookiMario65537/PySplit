from Widgets import WidgetBase
import threading
import asyncio
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.helper import AuthScope
from twitchAPI.chat import Chat, EventData, ChatEvent
import re
import logging

logger = logging.getLogger(__name__)

USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]


class Widget(WidgetBase.WidgetBase):
    def __init__(self, parent, state, config):
        super().__init__(parent, state, config)
        self.configure(bg="black")
        self.state = state
        self.config = config
        self.chat = None
        missing = []
        for key in ["targetChannel", "appId", "appSecret"]:
            if self.config[key] == "":
                missing.append(key)
        if len(missing):
            logger.warning(f"""Multi-Mario bot configuration is missing keys:
{'\n'.join(missing)}

For information on creating and registering a Twitch bot account (or adding bot
capabilities to your own Twitch account), see the developer instructions here:

https://dev.twitch.tv/docs/authentication/register-app/

"targetChannel" is the name the channel your bot should join (likely either the
name of your own channel or `MultiMarioEvents`), "appId" is the client ID from
the developer account settings, and "appSecret" is the client secret you create
in the developer account settings.""")
            return
        asyncio.run(self.run())

    def sendUpdate(self):
        split = self.state.splitnames[self.state.splitnum - 1]
        braces = re.findall(r'\[(.+?)\]', split)
        count = None
        for brace in braces:
            if brace.isdigit():
                count = brace
                break
        if count is None:
            return

        async def wrapper():
            await self.chat.send_message(
                self.config["targetChannel"],
                f"!set {count}")

        asyncio.run(wrapper())

    def onShutdown(self):
        if self.chat is None:
            return
        self.chat.stop()

    def onSplit(self):
        if self.chat is None:
            return
        thread = threading.Thread(target=self.sendUpdate)
        thread.start()

    async def onReady(self, ready_event: EventData):
        """
        This will be called when the event READY is triggered, which will be on
        bot start.
        """
        logger.info(f"Multi-Mario bot is ready for work, joining channel {self.config["targetChannel"]}")
        await ready_event.chat.join_room(self.config["targetChannel"])

    async def run(self):
        """
        Start the bot and set up the callback to enter the chat room.
        """
        twitch = await Twitch(self.config["appId"], self.config["appSecret"])
        auth = UserAuthenticator(twitch, USER_SCOPE)
        token, refresh_token = await auth.authenticate()
        await twitch.set_user_authentication(token, USER_SCOPE, refresh_token)

        self.chat = await Chat(twitch)
        self.chat.register_event(ChatEvent.READY, self.onReady)
        self.chat.start()
