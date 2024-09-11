# import contextlib
# from pathlib import PurePath
# from typing import Optional
#
# from textual import on
# from textual.app import ComposeResult
# from textual.containers import Container, Horizontal, Vertical, VerticalScroll, Widget
# from textual.css.query import NoMatches
# from textual.screen import ModalScreen
# from textual.validation import Number
# from textual.widgets import Button, Checkbox, Header, Input, Select, TextArea
# from paita.tui.error_screen import ErrorScreen
# import paita.localization.labels as label
# from paita.localization import labels
# from paita.settings.rag_settings import RAGSource, RAGSources
# from paita.settings.rag_settings import RAG, RAGSourceType
# from paita.settings.llm_settings import LLMSettings
# from paita.tui.wait_screen import WaitScreen
# from paita.utils.logger import log
# from paita.utils.string_utils import str_to_dict, str_to_num, validate_and_fix_url
#
# RAG_WIDGET_IDS = [
#     "ai_rag_type",
#     "ai_rag_source",
#     "ai_rag_source_max_depth",
#     "ai_rag_load",
#     "ai_rag_reset",
#     "ai_rag_contextualize_prompt",
#     "ai_rag_system_prompt",
# ]
#
#
# class RAGSettingsScreen(ModalScreen[bool]):
#     CSS_PATH = PurePath(__file__).parent / "styles" / "rag_settings_screen.tcss"
#
#     def __init__(
#         self,
#         *,
#         settings: LLMSettings,
#         rag: Optional[RAG],
#         allow_cancel: bool = False,
#     ):
#         super().__init__()
#         self.settings: LLMSettings = settings
#         self.rag: RAG = rag
#         self.settings.settings_model = settings.settings_model
#         self.allow_cancel: bool = allow_cancel
#
#
#     def compose(self) -> ComposeResult:
#         yield Header()
#         with Container(classes="llm_settings"):
#             with VerticalScroll(id="llm_settings"):
#                 with Vertical(classes="settings_invisible_block", id="ai_rag_container"):
#                     yield Checkbox(
#                         label.AI_RAG_ENABLED,
#                         value=self.rag.rag_model.rag_enabled,
#                         id="ai_rag_enabled",
#                         classes="settings_checkbox",
#                     )
#                     yield TextArea(
#                         text=self.rag.rag_model.rag_contextualize_prompt,
#                         id="ai_rag_contextualize_prompt",
#                         classes="settings_textarea",
#                     )
#                     yield TextArea(
#                         text=self.rag.rag_model.rag_system_prompt,
#                         id="ai_rag_system_prompt",
#                         classes="settings_textarea",
#                     )
#
#                 with Horizontal(classes="settings_block"):
#                     yield Button(label="Apply", variant="success", id="apply")
#                     if self.allow_cancel:
#                         yield Button(label="Cancel", variant="warning", id="cancel")
#
#     @staticmethod
#     def validate_ai_model_kwargs(value: str):
#         try:
#             str_to_dict(value)
#         except ValueError:
#             return False
#         else:
#             return True
#
#     async def on_mount(self) -> None:
#         # TODO: Create a separate component to handle RAG source(s)
#         self.query_one("#rag_contextualize_prompt").disabled = not self.rag.rag_model.rag_enabled
#         self.query_one("#rag_system_prompt").disabled = not self.rag.rag_model.rag_enabled
#
#         rag_source: RAGSource = RAGSource()
#         if self.rag is not None:
#             rag_sources: RAGSources = await self.rag.read()
#             if rag_sources.rag_sources:
#                 rag_source: RAGSource = rag_sources.rag_sources[-1]
#
#         widgets: [Widget] = [
#             Select(
#                 [(item.value, item.value) for item in RAGSourceType],
#                 value=rag_source.rag_source_type.value,
#                 prompt="AI Rag Type",
#                 id="ai_rag_type",
#                 classes="settings_small_option",
#                 allow_blank=False,
#                 disabled=not self.rag.rag_model.rag_enabled,
#             ),
#             Input(
#                 placeholder=label.AI_RAG_SOURCE_MAX_DEPTH,
#                 value=str(rag_source.rag_source_max_depth),
#                 id="ai_rag_source_max_depth",
#                 classes="settings_small_input",
#                 type="integer",
#                 validators=[Number(minimum=1, maximum=5)],
#                 max_length=1,
#                 disabled=not self.rag.rag_model.rag_enabled,
#             ),
#         ]
#
#         # ai_rag_source: not None
#         # - input = disable
#         # - button = "reset"
#         # ai_rag_source: None
#         # - input = enabled
#         # - button = "load"
#         input_disabled = not self.rag.rag_model.rag_enabled or bool(rag_source.rag_source)
#         ai_rag_source = Input(
#             placeholder=label.AI_RAG_SOURCE,
#             value=rag_source.rag_source if rag_source.rag_source else "",
#             id="ai_rag_source",
#             classes="settings_input",
#             disabled=input_disabled,
#         )
#         widgets.append(ai_rag_source)
#
#         button_disabled = not self.rag.rag_model.rag_enabled
#         if self.rag.rag_model.rag_enabled and ai_rag_source.value == "":
#             button_disabled = True
#         if bool(rag_source.rag_source):
#             widgets.append(Button(label="Reset", variant="warning", id="ai_rag_reset", disabled=button_disabled))
#         else:
#             widgets.append(Button(label="Load", variant="success", id="ai_rag_load", disabled=button_disabled))
#
#         horizontal = Horizontal(classes="settings_invisible_block", id="ai_rag_sources")
#         rag_container = self.query_one("#ai_rag_container")
#         await rag_container.mount(horizontal)
#         await horizontal.mount(*widgets)
#         self.query_one("#ai_persona").disabled = self.settings.settings_model.ai_rag_enabled
#
#     @on(Input.Changed)
#     async def input_changed(self, event: Input.Changed) -> None:
#         if event.input.id == "ai_rag_source":
#             try:
#                 ai_rag_load = self.query_one("#ai_rag_load")
#                 if event.input.value != "":
#                     ai_rag_load.disabled = False
#                 else:
#                     ai_rag_load.disabled = True
#             except NoMatches:
#                 pass
#
#     @on(Checkbox.Changed)
#     async def checkbox_changed(self, event: Checkbox.Changed) -> None:
#         if event.checkbox.id == "rag_enabled":
#             for rag_widget_id in RAG_WIDGET_IDS:
#                 with contextlib.suppress(NoMatches):
#                     self.query_one(f"#{rag_widget_id}").disabled = not event.checkbox.value
#
#             # Keep 'rag_settings source'-input field disabled when we think source is loaded
#             # If there's 'load'-button keep it disabled if 'rag_settings source' field has content
#             if event.checkbox.value:
#                 rag_source = self.query_one("#rag_source", Input)
#                 try:
#                     rag_load = self.query_one("#rag_load")
#                     if rag_source.value != "":
#                         rag_load.disabled = False
#                     else:
#                         rag_load.disabled = True
#                 except NoMatches:
#                     pass
#
#             self.query_one("#ai_persona").disabled = event.checkbox.value
#
#     @on(Select.Changed)
#     async def select_changed(self, event: Select.Changed) -> None:
#         if event.control.id == "rag_type":
#             pass  # TODO: Handle different RAG types
#         else:
#             log.error(f"Undefined {event.control.id=}")
#
#     async def on_button_pressed(self, event: Button.Pressed) -> None:
#         # RAG
#         self.rag.rag_model.rag_enabled = self.query_one("#rag_enabled", Input).value
#         if (value := self.query_one("#rag_contextualize_prompt", TextArea).text) != "":
#             self.rag.rag_model.rag_contextualize_prompt = value
#         if (value := self.query_one("#rag_system_prompt", TextArea).text) != "":
#             self.rag.rag_model.ai_rag_system_prompt = value
#
#         self.rag.rag_model = model
#
#         if event.button.id == "apply":
#             await self.settings.save()
#             await self.dismiss(True)
#         elif event.control.id == "ai_rag_load":
#             ai_rag_source = self.query_one("#ai_rag_source")
#             if (value := ai_rag_source.value) != "":
#                 try:
#                     url = validate_and_fix_url(value)
#                     ai_rag_source.remove_class("settings_input_error", update=True)
#                     ai_rag_source.value = url
#
#                     max_depth = str_to_num(self.query_one("#ai_rag_source_max_depth").value)
#                     await self.parent.push_screen(WaitScreen(labels.APP_RAG_PROCESS_DOCUMENTS))
#                     await self.rag.create(url=url, max_depth=max_depth)
#                     await event.control.remove()
#                     await self.mount(Button(label="Reset", variant="warning", id="ai_rag_reset"), after=ai_rag_source)
#
#                     await self.settings.save()
#                     self.parent.pop_screen()
#                 except ValueError as e:
#                     self.parent.pop_screen()
#                     ai_rag_source.add_class("settings_input_error", update=True)
#                     log.debug(f"{self.settings.settings_model.ai_service=} {self.settings.settings_model.ai_model=}")
#                     log.exception(e)
#                 except Exception as e:
#                     self.parent.pop_screen()
#                     error = str(e)
#                     log.exception(error)
#                     await self.parent.push_screen(ErrorScreen(error))
#                     ai_rag_source.add_class("settings_input_error", update=True)
#                     ai_rag_source.value = ""
#
#         elif event.control.id == "ai_rag_reset":
#             ai_rag_source = self.query_one("#ai_rag_source")
#             await self.rag.delete(ai_rag_source.value)
#             ai_rag_source.value = ""
#             ai_rag_source.disabled = False
#             await event.control.remove()
#             await self.mount(
#                 Button(label="Load", variant="success", id="ai_rag_load", disabled=True), after=ai_rag_source
#             )
#             await self.settings.save()
#         else:
#             self.dismiss(False)
