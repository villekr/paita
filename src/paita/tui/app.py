from enum import Enum
from pathlib import PurePath
from typing import TYPE_CHECKING, Union

from appdirs import user_config_dir
from cache3 import DiskCache
from textual.app import App, ComposeResult, Widget
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Footer, Header, Input, LoadingIndicator

from paita.llm.callbacks import AsyncHandler
from paita.llm.chat import Chat
from paita.llm.chat_history import ChatHistory
from paita.llm.enums import Tag
from paita.llm.models import list_all_models
from paita.localization import labels
from paita.tui.error_screen import ErrorScreen
from paita.tui.factory import create_rag_manager
from paita.tui.message_box import MessageBox
from paita.tui.multi_line_input import MultiLineInput
from paita.tui.settings_screen import SettingsScreen
from paita.tui.wait_screen import WaitScreen
from paita.utils.logger import log
from paita.utils.settings_manager import SettingsManager, SettingsModel

if TYPE_CHECKING:
    from paita.rag.rag_manager import RAGManager


class Role(Enum):
    QUESTION = "question"
    ANSWER = "answer"
    INFO = "info"
    ERROR = "error"


CACHE_DIR = user_config_dir(appname=labels.APP_TITLE, appauthor=labels.APP_AUTHOR)
CACHE_NAME = "cache"
CACHE_TTL = 24 * 60 * 60


TEXT_AREA = True


class ChatApp(App):
    TITLE = labels.APP_TITLE
    SUB_TITLE = labels.APP_SUBTITLE
    CSS_PATH = PurePath(__file__).parent / "styles" / "app.tcss"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", key_display="ctrl+q"),
        Binding("ctrl+x", "clear", "Clear", key_display="ctrl+x"),
        Binding("ctrl+p", "settings", "Settings", key_display="ctrl+p"),
    ]

    def __init__(self):
        super().__init__()

        self._settings_manager: SettingsManager = None
        self._rag_manager: RAGManager = None
        self._chat: Chat = None
        self._cache: DiskCache = DiskCache(CACHE_DIR, CACHE_NAME)

        self._current_message: Union[MessageBox or None] = None
        self._current_id: str = "id_0"
        self._last_focused: Union[Widget or None] = None

        self._chat_history = ChatHistory(app_name=labels.APP_TITLE, app_author=labels.APP_AUTHOR)

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
                yield Button("Send", variant="success", id="send_button")
        yield Footer()

    # Action handlers

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send_button":
            await self.process_conversation()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id in ("input", "multi_line_input"):
            await self.process_conversation()

    def action_settings(self, allow_cancel: bool = False) -> None:  # noqa: FBT001, FBT002
        settings_screen = SettingsScreen(
            settings_manager=self._settings_manager,
            rag_manager=self._rag_manager,
            cache=self._cache,
            allow_cancel=allow_cancel,
        )
        callback = self.exit_settings
        log.info(f"{callback=}")
        self.push_screen(
            screen=settings_screen,
            callback=callback,
        )

    async def action_clear(self) -> None:
        await self._chat_history.history.aclear()
        await self.query_one("#conversation").remove()
        await self.query_one("#body").mount(VerticalScroll(id="conversation"))

    def action_quit(self) -> None:
        self._cache.clear()
        self.exit()

    # Callbacks

    def exit_settings(self, changed: bool = False):  # noqa: FBT001, FBT002
        if changed:
            self.init_chat()

    async def on_mount(self) -> None:
        await self._mount_chat_history()
        try:
            await self.push_screen(WaitScreen(labels.APP_LIST_AI_SERVICES_MODELS))
            await self._list_models()
            self.pop_screen()
        except ValueError as e:
            log.error(e)
            self.pop_screen()
            await self.push_screen(
                ErrorScreen(
                    labels.APP_ERROR_NO_AI_SERVICES_OR_MODELS,
                    labels.APP_DIALOG_BUTTON_EXIT,
                ),
                self.exit,
            )
            return
        # Read existing settings or open settings screen
        try:
            self._settings_manager: SettingsManager = await SettingsManager.load(
                app_name=labels.APP_TITLE, app_author=labels.APP_AUTHOR
            )
            self._rag_manager = create_rag_manager(
                app_name=labels.APP_TITLE,
                app_author=labels.APP_AUTHOR,
                settings_model=self._settings_manager.model,
                cache=self._cache,
            )
            await self._rag_manager.read()
            self.init_chat()
        except FileNotFoundError:
            self._settings_manager = SettingsManager(
                model=SettingsModel(),
                app_name=labels.APP_TITLE,
                app_author=labels.APP_AUTHOR,
            )
            self._rag_manager = create_rag_manager(
                app_name=labels.APP_TITLE,
                app_author=labels.APP_AUTHOR,
                settings_model=self._settings_manager.model,
                cache=self._cache,
            )
            await self._rag_manager.read()
            self.action_settings(allow_cancel=False)

    def init_chat(self):
        if self._chat is None:
            self._chat = Chat()
        callback_handler = AsyncHandler()
        callback_handler.register_callbacks(self.callback_on_token, self.callback_on_end, self.callback_on_error)

        try:
            self._chat.init_model(
                settings_model=self._settings_manager.model,
                chat_history=self._chat_history,
                rag_manager=self._rag_manager,
                callback_handler=callback_handler,
            )
            if TEXT_AREA:
                self.query_one("#multi_line_input").focus()
            else:
                self.query_one("#input").focus()
        except ValueError:
            self._settings_manager = SettingsManager(
                model=SettingsModel(),
                app_name=labels.APP_TITLE,
                app_author=labels.APP_AUTHOR,
            )
            self.action_settings(allow_cancel=False)

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
        conversation.scroll_end(animate=False)

        try:
            await self._chat.request(question)
        except ValueError as e:
            error = str(e)
            log.info(error)
            self.push_screen(ErrorScreen(error), self.exit_error_screen)
        except Exception as e:  # noqa: BLE001
            error = str(e)
            log.exception(e)
            self.push_screen(ErrorScreen(error), self.exit_error_screen)

    def toggle_widgets(self, *widgets: Widget) -> None:
        for w in widgets:
            w.disabled = not w.disabled

    def callback_on_token(self, data: str):
        if self._current_message is None:
            loading_indication = self.query_one(LoadingIndicator)
            loading_indication.remove()
            self._current_message = MessageBox(data, role="answer")
            conversation = self.query_one("#conversation")
            conversation.mount(self._current_message)
        else:
            self._current_message.append(data)

    def callback_on_end(self, data: str):
        conversation = self.query_one("#conversation")
        if self._current_message is None:
            loading_indication = self.query_one(LoadingIndicator)
            loading_indication.remove()
            self._current_message = MessageBox(data, role="answer")
            conversation.mount(self._current_message)

        self._current_message.flush()
        self._current_message = None

        text_input = self.query_one("#multi_line_input") if TEXT_AREA else self.query_one("#input")
        button = self.query_one("#send_button")
        self.toggle_widgets(text_input, button)
        text_input.focus()

    def callback_on_error(self, error):
        if self._current_message:
            loading_indication = self.query_one(LoadingIndicator)
            loading_indication.remove()
            self._current_message.flush()
            self._current_message = None

        self.push_screen(ErrorScreen(str(error)), self.exit_error_screen)

    def exit_error_screen(self, exit_app: bool = False):  # noqa: FBT001, FBT002
        if exit_app:
            self.exit()

        loading_indication = self.query_one(LoadingIndicator)
        loading_indication.remove()

        text_input = self.query_one("#multi_line_input") if TEXT_AREA else self.query_one("#input")
        button = self.query_one("#send_button")
        self.toggle_widgets(text_input, button)

        text_input.focus()

    async def _mount_chat_history(self):
        messages = await self._chat_history.messages()
        message_boxes: [MessageBox] = [
            MessageBox(data=message.content, role=message.role.value) for message in messages
        ]
        conversation = self.query_one("#conversation")
        await conversation.mount_all(message_boxes)
        conversation.scroll_end(animate=False)

    async def _list_models(self):
        self.push_screen(WaitScreen(labels.APP_LIST_AI_SERVICES_MODELS))
        all_models = await list_all_models()
        self.pop_screen()
        not_none_ai_models = any(len(models) for models in all_models.values())
        if not not_none_ai_models:
            msg = "No models found"
            raise ValueError(msg)
        for key in all_models:
            if all_models[key]:
                self._cache.set(key, all_models[key], CACHE_TTL, tag=Tag.AI_MODELS.value)


def main():
    app = ChatApp()
    app.run()


if __name__ == "__main__":
    main()
