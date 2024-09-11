import os
from enum import Enum
from pathlib import PurePath
from typing import Optional, Union

from appdirs import user_config_dir
from textual.app import App, ComposeResult, Widget
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Footer, Header, Input, LoadingIndicator

from paita.llm.callbacks import AsyncHandler
from paita.llm.chat import Chat
from paita.llm.chat_history import ChatHistory
from paita.llm.services.service import LLMSettingsModel
from paita.localization import labels
from paita.settings.llm_settings import LLMSettings

# from paita.settings.models import RAGModel
from paita.tui.error_screen import ErrorScreen
from paita.tui.llm_settings_screen import LLMSettingsScreen
from paita.tui.message_box import MessageBox
from paita.tui.multi_line_input import MultiLineInput

# from paita.tui.rag_settings_screen import RAGSettingsScreen
from paita.tui.wait_screen import WaitScreen
from paita.utils.logger import log


class Role(Enum):
    QUESTION = "question"
    ANSWER = "answer"
    INFO = "info"
    ERROR = "error"


TEXT_AREA = True


class ChatApp(App):
    TITLE = labels.APP_TITLE
    SUB_TITLE = labels.APP_SUBTITLE
    CSS_PATH = PurePath(__file__).parent / "styles" / "app.tcss"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", key_display="ctrl+q"),
        Binding("ctrl+x", "clear", "Clear", key_display="ctrl+x"),
        Binding("ctrl+1", "llm_settings", "LLM Settings", key_display="ctrl+1"),
    ]

    def __init__(self):
        super().__init__()

        self.settings: Optional[LLMSettings] = None
        # self.rag: Optional[RAGModel] = None
        config_dir = user_config_dir(appname=labels.APP_TITLE, appauthor=labels.APP_AUTHOR)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        self._chat_history = ChatHistory(app_name=labels.APP_TITLE, app_author=labels.APP_AUTHOR)

        self._chat: Optional[Chat] = None

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
                yield Button("Send", variant="success", id="send_button")
        yield Footer()

    # Action handlers

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send_button":
            await self.process_conversation()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id in ("input", "multi_line_input"):
            await self.process_conversation()

    def action_llm_settings(self, allow_cancel: bool = False) -> None:  # noqa: FBT001, FBT002
        settings_screen = LLMSettingsScreen(
            settings=self.settings,
            allow_cancel=allow_cancel,
        )
        callback = self.exit_settings
        log.info(f"{callback=}")
        self.push_screen(
            screen=settings_screen,
            callback=callback,
        )

    # def action_rag_settings(self, allow_cancel: bool = False) -> None:
    #     settings_screen = RAGSettingsScreen(
    #         settings=self.settings,
    #         allow_cancel=allow_cancel,
    #     )
    #     callback = self.exit_settings
    #     log.info(f"{callback=}")
    #     self.push_screen(
    #         screen=settings_screen,
    #         callback=callback,
    #     )

    async def action_clear(self) -> None:
        await self._chat_history.history.aclear()
        await self.query_one("#conversation").remove()
        await self.query_one("#body").mount(VerticalScroll(id="conversation"))

    def action_quit(self) -> None:
        self.settings.cache.clear()
        self.exit()

    # Callbacks

    def exit_settings(self, changed: bool = False):  # noqa: FBT001, FBT002
        if changed:
            self.init_chat()

    # def exit_rag_settings(self, changed: bool = False):
    #     if changed:
    #         self.rag = RAGModel.create_rag(
    #             app_name=labels.APP_TITLE,
    #             app_author=labels.APP_AUTHOR,
    #             settings_model=self.settings.settings_model,
    #         )
    #         self.init_chat()

    async def on_mount(self):
        await self._mount_chat_history()
        await self.push_screen(WaitScreen(labels.APP_LIST_AI_SERVICES_MODELS))

        settings_exists = False
        try:
            self.settings: LLMSettings = await LLMSettings.load(app_name=labels.APP_TITLE, app_author=labels.APP_AUTHOR)
            settings_exists = True
        except FileNotFoundError:
            self.settings = LLMSettings(
                app_name=labels.APP_TITLE,
                app_author=labels.APP_AUTHOR,
            )

        try:
            await self.settings.refresh_llms()
        except ValueError as e:
            log.error(e)
            await self.pop_screen()
            await self.push_screen(
                ErrorScreen(
                    labels.APP_ERROR_NO_AI_SERVICES_OR_MODELS,
                    labels.APP_DIALOG_BUTTON_EXIT,
                ),
                self.exit,
            )
            return

        await self.pop_screen()
        if settings_exists:
            # self.rag = RAGModel.create_rag(
            #     app_name=labels.APP_TITLE,
            #     app_author=labels.APP_AUTHOR,
            #     settings_model=self.settings.settings_model,
            # )
            self.init_chat()
        else:
            self.action_llm_settings(allow_cancel=False)

    def init_chat(self):
        if self._chat is None:
            self._chat = Chat()

        callback_handler = AsyncHandler()
        callback_handler.register_callbacks(self.callback_on_token, self.callback_on_end, self.callback_on_error)

        try:
            self._chat.init_model(
                settings_model=self.settings.model,
                chat_history=self._chat_history,
                # rag=self.rag,
                callback_handler=callback_handler,
            )
            if TEXT_AREA:
                self.query_one("#multi_line_input").focus()
            else:
                self.query_one("#input").focus()
        except ValueError:
            self.settings = LLMSettings(
                settings_model=LLMSettingsModel(),
                app_name=labels.APP_TITLE,
                app_author=labels.APP_AUTHOR,
            )
            # self.rag = RAGModel.create_rag(
            #     app_name=labels.APP_TITLE,
            #     app_author=labels.APP_AUTHOR,
            #     settings_model=self.settings.model,
            # )
            self.action_llm_settings(allow_cancel=False)

    async def process_conversation(self) -> None:
        if TEXT_AREA:
            text_input: MultiLineInput = self.query_one("#multi_line_input", MultiLineInput)
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
            await self.push_screen(ErrorScreen(error), self.exit_error_screen)
        except Exception as e:  # noqa: BLE001
            error = str(e)
            log.exception(e)
            await self.push_screen(ErrorScreen(error), self.exit_error_screen)

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


def main():
    app = ChatApp()
    app.run()


if __name__ == "__main__":
    main()
