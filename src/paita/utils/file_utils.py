from pathlib import Path

from aiofiles import os as aiofiles_os
from paita.utils.logger import log


async def delete_folder(folder_path: Path, *, recursive: bool = False, dry_run: bool = False) -> None:
    if recursive:
        for file in await aiofiles_os.listdir(folder_path):
            path = folder_path / file
            is_file = await aiofiles_os.path.isfile(path)
            is_folder = await aiofiles_os.path.isdir(path)
            log.debug(f"{is_file=} {is_folder=}")
            if is_file:
                if not dry_run:
                    await aiofiles_os.remove(path)
            elif is_folder:
                await delete_folder(path, recursive=recursive, dry_run=dry_run)
            else:
                pass

    if not dry_run:
        await aiofiles_os.rmdir(folder_path)
