import asyncio

from paita.utils.logger import log

markdown_content = [
    "# Sample Markdown Content\n",
    "\n",
    "This is a simple example of using Markdown in a list:\n",
    "\n",
    "- **Bold Text**: **This is bold text**\n",
    "- *Italic Text*: *This is italic text*\n",
    "- [Link](https://www.example.com): \n" "- Click [here](https://www.example.com) for more information\n",
    "- Bullet Points:\n",
    "  - Point 1\n",
    "  - Point 2\n",
    "- Numbered List:\n",
    "  1. First item\n",
    "  2. Second item\n",
    "\n",
    "Feel free to customize and add more elements to suit your needs!",
]


class MockModel:
    async def request(self, data: str) -> str:
        log.debug(data)
        if self.streaming:
            await asyncio.sleep(2)  # initial request sleep
            for item in markdown_content:
                self.callback_on_token(item)
                await asyncio.sleep(0.2)
        else:
            self.callback_on_token(markdown_content)
        self.callback_on_end()

    async def streaming(self):
        await asyncio.sleep(2)  # initial request sleep
        for item in markdown_content:
            self.callback_on_token(item)
            await asyncio.sleep(0.2)
