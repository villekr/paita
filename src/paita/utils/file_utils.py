from pathlib import Path

from aiofiles import os as aiofiles_os

from paita.utils.logger import log


async def delete_folder(folder_path: Path, *, recursive: bool = False, dry_run: bool = False) -> None:
    if recursive:
        for file in await aiofiles_os.listdir(folder_path):
            path = folder_path / file
            if aiofiles_os.path.isfile(path):
                log.debug(f"remove: {path=}")
                if not dry_run:
                    await aiofiles_os.remove(path)
            elif aiofiles_os.path.isfile(path):
                await delete_folder(path, recursive=recursive, dry_run=dry_run)
            else:
                pass

    log.debug(f"rmdir: {folder_path=}")
    if not dry_run:
        await aiofiles_os.rmdir(folder_path)
