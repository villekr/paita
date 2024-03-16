from langchain.callbacks.base import AsyncCallbackHandler, BaseCallbackHandler
from langchain.schema.output import LLMResult


class SyncHandler(BaseCallbackHandler):
    callback_on_token = None
    callback_on_end = None

    def register_callbacks(self, callback_on_token, callback_on_end):
        self.callback_on_token = callback_on_token
        self.callback_on_end = callback_on_end

    def on_llm_new_token(self, token: str) -> None:
        self.callback_on_token(token)

    def on_llm_end(self, response: LLMResult) -> None:
        self.callback_on_end(response)


class AsyncHandler(AsyncCallbackHandler):
    # callback_on_start = None
    callback_on_token = None
    callback_on_end = None
    callback_on_error = None

    def register_callbacks(
        self,
        # callback_on_start,
        callback_on_token,
        callback_on_end,
        callback_on_error,
    ):
        # self.callback_on_start = callback_on_start
        self.callback_on_token = callback_on_token
        self.callback_on_end = callback_on_end
        self.callback_on_error = callback_on_error

    # From base class
    # async def on_chat_model_start(
    #     self,
    #     serialized: Dict[str, Any],
    #     messages: List[List[BaseMessage]],
    #     *,
    #     run_id: UUID,
    #     parent_run_id: Optional[UUID] = None,
    #     tags: Optional[List[str]] = None,
    #     metadata: Optional[Dict[str, Any]] = None,
    #     **kwargs: Any,
    # ) -> Any:
    #     # log.debug(
    #     #     f"{serialized=} {messages=} {run_id=} {parent_run_id=} {tags=} {metadata=}"
    #     # )
    #     pass

    async def on_llm_new_token(
        self,
        token: str,
        # *,
        # chunk: Optional[Union[GenerationChunk, ChatGenerationChunk]] = None,
        # run_id: UUID,
        # parent_run_id: Optional[UUID] = None,
        # tags: Optional[List[str]] = None,
        # **kwargs: Any,
        **kwargs,  # noqa: ARG002
    ) -> None:
        # log.debug(f"{token=} {chunk=} {run_id=} {parent_run_id=} {tags=}")
        self.callback_on_token(token)

    async def on_llm_end(
        self,
        response: LLMResult,
        # *,
        # run_id: UUID,
        # parent_run_id: Optional[UUID] = None,
        # tags: Optional[List[str]] = None,
        # **kwargs: Any,
        **kwargs,  # noqa: ARG002
    ) -> None:
        # log.debug(f"{response=} {run_id=} {parent_run_id=} {tags=}")
        output = response.flatten().pop().generations.pop().pop().text
        self.callback_on_end(output)

    async def on_llm_error(
        self,
        error: BaseException,
        # *,
        # run_id: UUID,
        # parent_run_id: Optional[UUID] = None,
        # tags: Optional[List[str]] = None,
        # **kwargs: Any,
        **kwargs,  # noqa: ARG002
    ) -> None:
        # log.error(f"{error=} {run_id=} {parent_run_id=} {tags=}")
        self.callback_on_error(error)
