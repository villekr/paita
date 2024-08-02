from pathlib import PurePath

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.validation import Function, Number
from textual.widgets import Button, Checkbox, Header, Input, Select, TextArea
import paita.localization.labels as label
from paita.settings.llm_settings.llm_settings import LLMSettings, LLMSettingsModel
from paita.utils.logger import log
from paita.utils.string_utils import dict_to_str, str_to_dict, str_to_num, to_str


class LLMSettingsScreen(ModalScreen[bool]):
    CSS_PATH = PurePath(__file__).parent / "styles" / "llm_settings_screen.tcss"

    def __init__(
        self,
        *,
        settings: LLMSettings,
        allow_cancel: bool = False,
    ):
        super().__init__()
        self.settings: LLMSettings = settings
        self.settings.settings_model = settings.settings_model.model_copy()
        self.allow_cancel: bool = allow_cancel

        self.available_ai_services = self.settings.available_ai_services()
        self.available_ai_models = self.settings.available_ai_models(self.settings.settings_model.ai_service, None)
        log.debug(f"{self.available_ai_services=} {self.available_ai_models=}")

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="llm_settings"):
            with VerticalScroll(id="llm_settings"):
                with Horizontal(classes="settings_invisible_block"):
                    yield Select(
                        [(item, item) for item in self.available_ai_services],
                        value=self.settings.settings_model.ai_service,
                        prompt="AI Service",
                        id="ai_service",
                        classes="settings_small_option",
                        allow_blank=False,
                    )
                    yield Select(
                        [(item, item) for item in self.available_ai_models],
                        value=self.settings.settings_model.ai_model,
                        prompt="AI Model",
                        id="ai_model",
                        classes="settings_option",
                        allow_blank=False,
                    )
                    yield Checkbox(
                        label.AI_STREAMING,
                        value=self.settings.settings_model.ai_streaming,
                        id="ai_streaming",
                        classes="settings_checkbox",
                    )
                    # yield Button(label="Refresh", variant="success", id="ai_refresh")  # TODO: ai refresh

                yield TextArea(
                    text=self.settings.settings_model.ai_persona,
                    id="ai_persona",
                    classes="settings_textarea",
                )

                with Horizontal(classes="settings_invisible_block"):
                    yield Input(
                        placeholder=label.AI_MODEL_KWARGS,
                        value=dict_to_str(self.settings.settings_model.ai_model_kwargs),
                        id="ai_model_kwargs",
                        classes="settings_input",
                        validators=[Function(self.validate_ai_model_kwargs, "Invalid dictionary")],
                    )
                    yield Input(
                        placeholder=label.AI_MAX_TOKENS,
                        value=to_str(self.settings.settings_model.ai_max_tokens),
                        id="ai_max_tokens",
                        classes="settings_small_input",
                        type="integer",
                        validators=[Number(minimum=1, maximum=9999999999)],
                        max_length=10,
                    )
                    yield Input(
                        placeholder=label.AI_HISTORY_DEPTH,
                        value=to_str(self.settings.settings_model.ai_history_depth),
                        id="ai_history_depth",
                        classes="settings_small_input",
                        type="integer",
                        validators=[Number(minimum=0, maximum=100)],
                        max_length=3,
                    )
                    # yield Input(
                    #     placeholder=label.AI_N,
                    #     value=to_str(self.llm_settings.settings_model.ai_n),
                    #     id="ai_n",
                    #     classes="settings_input",
                    #     type="integer",
                    #     validators=[Number(minimum=1, maximum=10)],
                    #     max_length=4,
                    # )

                with Horizontal(classes="settings_block"):
                    yield Button(label="Apply", variant="success", id="apply")
                    if self.allow_cancel:
                        yield Button(label="Cancel", variant="warning", id="cancel")

    @staticmethod
    def validate_ai_model_kwargs(value: str):
        try:
            str_to_dict(value)
        except ValueError:
            return False
        else:
            return True

    async def on_mount(self) -> None:
        if (
            self.settings.settings_model.ai_service is Select.BLANK
            or self.settings.settings_model.ai_model is Select.BLANK
        ):
            self.query_one("#apply").disabled = True

    @on(Checkbox.Changed)
    async def checkbox_changed(self, event: Checkbox.Changed) -> None:
            self.query_one("#ai_persona").disabled = event.checkbox.value

    @on(Select.Changed)
    async def select_changed(self, event: Select.Changed) -> None:
        if event.control.id == "ai_service":
            value = event.value
            if value == self.settings.settings_model.ai_service:
                return
            self.settings.ai_service = value

            log.debug(f"{event.value}")
            models = self.settings.available_ai_models(event.value, Select.BLANK)
            widget: Select = self.query_one("#ai_model")
            widget.set_options((item, item) for item in models)
        elif event.control.id == "ai_model":
            value = event.value
            if value == self.settings.settings_model.ai_model:
                return
            self.settings.ai_model = value
            self.query_one("#apply").disabled = False
        else:
            log.error(f"Undefined {event.control.id=}")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        # if event.button.id == "ai_refresh":  # TODO: ai refresh
        #     await self.parent.push_screen(WaitScreen(labels.APP_LIST_AI_SERVICES_MODELS))
        #     await self.llm_settings.refresh_llms()
        #     available_ai_services = self.llm_settings.available_ai_services()
        #     ai_service: Select = self.query_one("#ai_service")
        #     current_ai_service = ai_service.value
        #     ai_service.set_options((item, item) for item in available_ai_services)
        #     ai_service.value = current_ai_service
        #     self.parent.pop_screen()
        #     return

        # PoC RAG approach, we always update model and save
        model: LLMSettingsModel = LLMSettingsModel(
            ai_service=self.query_one("#ai_service").value,
            ai_model=self.query_one("#ai_model").value,
        )
        if (value := self.query_one("#ai_persona").text) != "":
            model.ai_persona = value
        if (value := self.query_one("#ai_model_kwargs").value) != "":
            model.ai_model_kwargs = str_to_dict(value)
        model.ai_streaming = self.query_one("#ai_streaming").value
        # if (value := self.query_one("#ai_n").value) != "":
        #     model.ai_n = str_to_num(value)
        if (value := self.query_one("#ai_max_tokens").value) != "":
            model.ai_max_tokens = str_to_num(value)
        if (value := self.query_one("#ai_history_depth").value) != "":
            model.ai_history_depth = str_to_num(value)

        self.settings.settings_model = model

        if event.button.id == "apply":
            await self.settings.save()
            self.dismiss(True)
        else:
            self.dismiss(False)
