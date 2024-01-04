import aiofiles


async def append_file(folder: str,
                      content: str) -> None:
    async with aiofiles.open(file=folder,
                             mode='a',
                             encoding='utf-8-sig') as file:
        await file.write(f'{content}\n')
