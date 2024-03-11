from enum import Enum
from pathlib import PurePath
from typing import Union

from appdirs import user_config_dir
from cache3 import DiskCache
from textual.app import App, ComposeResult, Widget
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Footer, Header, Input, LoadingIndicator

import paita.localization.labels as label
from paita.ai.callbacks import AsyncHandler
from paita.ai.chat import Chat
from paita.ai.enums import Tag
from paita.ai.models import list_all_models
from paita.tui.error_screen import ErrorScreen
from paita.tui.message_box import MessageBox
from paita.tui.multi_line_input import MultiLineInput
from paita.tui.settings_screen import SettingsScreen
from paita.tui.wait_screen import WaitScreen
from paita.utils.logger import log
from paita.utils.settings_manager import SettingsManager, SettingsModel


class Role(Enum):
    QUESTION = "question"
    ANSWER = "answer"
    INFO = "info"
    ERROR = "error"


CACHE_DIR = user_config_dir(appname=label.APP_TITLE, appauthor=label.APP_AUTHOR)
CACHE_NAME = "cache"
CACHE_TTL = 24 * 60 * 60


TEXT_AREA = True


class ChatApp(App):
    TITLE = label.APP_TITLE
    SUB_TITLE = label.APP_SUBTITLE
    CSS_PATH = PurePath(__file__).parent / "styles" / "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", key_display="Q / CTRL+C"),
        ("ctrl+x", "clear", "Clear"),
        ("ctrl+1", "settings", "Settings"),
    ]

    _settings: SettingsManager = None
    _chat: Chat = None
    _cache: DiskCache = DiskCache(CACHE_DIR, CACHE_NAME)

    def __init__(self):
        super().__init__()
        self._current_message: Union[MessageBox or None] = None
        self._current_id: str = "id_0"
        self._last_focused: Union[Widget or None] = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="body"):
            vertical_scroll: VerticalScroll = VerticalScroll(id="conversation")
            vertical_scroll.can_focus = False
            yield vertical_scroll
            with Horizontal(id="input_box"):
                if TEXT_AREA:
                    yield MultiLineInput(id="multi_line_input", multiline=True)
                else:
                    yield Input(id="input")
                yield Button(label="Send", variant="success", id="send_button")
        yield Footer()

    # Action handlers

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "send_button":
            await self.process_conversation()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Event handler called when an input is submitted."""
        if event.input.id == "input" or event.input.id == "multi_line_input":
            await self.process_conversation()

    def action_settings(self, allow_cancel: bool = False) -> None:
        self.push_screen(
            SettingsScreen(
                settings=self._settings,
                cache=self._cache,
                allow_cancel=allow_cancel,
            ),
            self.exit_settings,
        )

    def action_clear(self) -> None:
        self.query_one("#conversation").remove()
        self.query_one("#body").mount(VerticalScroll(id="conversation"))

    def action_quit(self) -> None:
        self._cache.clear()
        self.exit()

    # Callbacks

    def exit_settings(self, changed: bool = False):
        if changed:
            self.init_chat()

    async def on_mount(self) -> None:
        # List all models from each supported AI Service
        # Add to cache: the models only from the AI Services that env has access to
        self.push_screen(WaitScreen(label.APP_LIST_AI_SERVICES_MODELS))
        models = await list_all_models()
        self.pop_screen()
        not_none_ai_models = any(value is not None for value in models.values())
        if not not_none_ai_models:
            self.push_screen(
                ErrorScreen(
                    label.APP_ERROR_NO_AI_SERVICES_OR_MODELS,
                    label.APP_DIALOG_BUTTON_EXIT,
                ),
                self.exit,
            )
            return

        for key in models.keys():
            if models[key]:
                self._cache.set(key, models[key], CACHE_TTL, tag=Tag.AI_MODELS.value)

        # Read existing settings or open settings screen
        try:
            self._settings: SettingsManager = await SettingsManager.load(
                app_name=label.APP_TITLE, app_author=label.APP_AUTHOR
            )
            self.init_chat()
        except FileNotFoundError:
            self._settings = SettingsManager(
                model=SettingsModel(),
                app_name=label.APP_TITLE,
                app_author=label.APP_AUTHOR,
            )
            self.action_settings(allow_cancel=False)

    def init_chat(self):
        if self._chat is None:
            self._chat = Chat(app_name=label.APP_TITLE, app_author=label.APP_AUTHOR)
        callback_handler = AsyncHandler()
        callback_handler.register_callbacks(
            self.callback_on_token, self.callback_on_end, self.callback_on_error
        )
        self._chat.init_model(
            settings_model=self._settings.model, callback_handler=callback_handler
        )
        if TEXT_AREA:
            self.query_one("#multi_line_input").focus()
        else:
            self.query_one("#input").focus()

    async def process_conversation(self) -> None:
        if TEXT_AREA:
            text_input: MultiLineInput = self.query_one("#multi_line_input")
            question = text_input.text
        else:
            text_input: Input = self.query_one("#input", Input)
            question = text_input.value

        if question == "":
            return

        button = self.query_one("#send_button")
        conversation = self.query_one("#conversation")

        self.toggle_widgets(text_input, button)

        with text_input.prevent(Input.Changed):
            if TEXT_AREA:
                text_input.text = ""
            else:
                text_input.value = ""

        await conversation.mount(
            MessageBox(question, role="question"),
            LoadingIndicator(),
        )

        try:
            await self._chat.request(question)
        except Exception as e:
            log.exception(e)

    def toggle_widgets(self, *widgets: Widget) -> None:
        for w in widgets:
            w.disabled = not w.disabled

    def callback_on_token(self, data: str):
        log.debug(f"callback_on_token: {data}")
        if self._current_message is None:
            loading_indication = self.query_one(LoadingIndicator)
            loading_indication.remove()
            self._current_message = MessageBox(data, role="answer")  # noqa: E501
            conversation = self.query_one("#conversation")
            conversation.mount(self._current_message)
        else:
            self._current_message.append(data)

    def callback_on_end(self, data: str):
        log.debug(f"callback_on_end: {data}")
        if self._current_message is None:
            log.debug("1")
            loading_indication = self.query_one(LoadingIndicator)
            loading_indication.remove()
            self._current_message = MessageBox(data, role="answer")  # noqa: E501
            conversation = self.query_one("#conversation")
            conversation.mount(self._current_message)

        log.debug("2")
        self._current_message.flush()
        self._current_message = None

        if TEXT_AREA:
            log.debug("3")
            text_input = self.query_one("#multi_line_input")
        else:
            text_input = self.query_one("#input")
        log.debug("4")
        button = self.query_one("#send_button")
        self.toggle_widgets(text_input, button)
        log.debug("5")
        text_input.focus()
        log.debug("6")

    def callback_on_error(self, error):
        if self._current_message:
            loading_indication = self.query_one(LoadingIndicator)
            loading_indication.remove()
            self._current_message.flush()
            self._current_message = None

        self.push_screen(ErrorScreen(str(error)), self.exit_error_screen)

    def exit_error_screen(self, exit_app: bool = False):
        try:
            loading_indication = self.query_one(LoadingIndicator)
            loading_indication.remove()
        except Exception as e:
            log.exception(e)

        if TEXT_AREA:
            text_input = self.query_one("#multi_line_input")
        else:
            text_input = self.query_one("#input")
        button = self.query_one("#send_button")
        self.toggle_widgets(text_input, button)

        if TEXT_AREA:
            self.query_one("#multi_line_input").focus()
        else:
            self.query_one("#input").focus()

    def _next_id(self) -> str:
        token = int(self._current_id.split("_")[1])
        token += 1
        self._current_id = f"id_{token}"
        return self._current_id


def main():
    app = ChatApp()
    app.run()


if __name__ == "__main__":
    main()
