import asyncio
import logging
from time import sleep
from humanize import naturalsize
from json import loads

import aiofiles
from tqdm import tqdm
from httpx import AsyncClient
from lxml import html

FORMAT = "%(levelname)s:\t%(message)s"
TOTAL, TASK_NUM, TOTAL_TASKS = 0, 0, 0

logging.basicConfig(format=FORMAT, level=logging.INFO)

# An async downloader
async def download(_publisher: str, _extension: str, progress: tqdm) -> None:
    """Download extensions"""
    global TASK_NUM

    async with AsyncClient(
        base_url="https://marketplace.visualstudio.com",
        http2=True,
        follow_redirects=True,
        timeout=None,
    ) as conn:
        response = await conn.get(
            "/items", params={"itemName": _publisher + "." + _extension}
        )
        tree: html.HtmlElement = html.fromstring(response.content)
        json_content: dict = loads(
            tree.find('.//div[@class="rhs-content"]/script').text
        )
        version: str = json_content["Resources"]["Version"]
        logging.debug({_publisher, _extension, version})
        total: int = 0

        while True:
            try:
                async with aiofiles.open(
                    f"extensions/{_publisher.lower()}-{_extension.lower()}.vsix", "wb"
                ) as output_buf:
                    async with conn.stream(
                        "GET",
                        f"/_apis/public/gallery/publishers/{_publisher}/vsextensions/{_extension}/{version}/vspackage",
                    ) as resp:
                        total = int(resp.headers["content-length"])
                        progress.total += total
                        bytes_downloaded = resp.num_bytes_downloaded
                        logging.debug(
                            f"Downloading {_publisher}.{_extension} - {version} | size: {naturalsize(resp.headers['content-length'])}"
                        )

                        async for chunk in resp.aiter_bytes():
                            progress.update(
                                resp.num_bytes_downloaded - bytes_downloaded
                            )

                            bytes_downloaded = resp.num_bytes_downloaded
                            await output_buf.write(chunk)

                TASK_NUM += 1
                progress.desc = f"Task completed {TASK_NUM}/{TOTAL_TASKS}"
                break
            except Exception as exception:
                progress.total -= total
                logging.error(f"{exception} | {_publisher}.{_extension} - {version} ")
                TASK_NUM -= 1
                sleep(10)

        ## Original Location
        # with open(
        #     f"{os.getenv('HOME')}/extensions/{_publisher.lower()}-{_extension.lower()}.vsix",
        #     "wb",
        # ) as data:
        #     data.write(
        #         conn.get(
        #             f"/_apis/public/gallery/publishers/{_publisher}/vsextensions/{_extension}/{version}/vspackage"
        #         ).content
        #     )


# Load list of extensions
with open("scripts/exts", "r", encoding="utf-8") as read_buf:
    extensions = loads(read_buf.read())


if __name__ == "__main__":
    download_tasks = []
    loop = asyncio.new_event_loop()

    progress = tqdm(
        total=TOTAL,
        bar_format=None,
        desc="",
        unit_scale=True,
        unit_divisor=1024,
        unit="B",
        leave=False,
    )
    # global TOTAL_TASKS

    for publisher, extension in extensions.items():
        if isinstance(extension, list):
            for ext in extension:
                download_tasks.append(
                    loop.create_task(download(publisher, ext, progress))
                )
                TOTAL_TASKS += 1
        else:
            download_tasks.append(
                loop.create_task(download(publisher, extension, progress))
            )
            TOTAL_TASKS += 1

    progress.desc = f"Task completed {TASK_NUM}/{TOTAL_TASKS}"

    loop.run_until_complete(asyncio.gather(*download_tasks))

