import os
from json import loads

from httpx import Client
from lxml import html

extensions = {
    "ms-python": ["pylint", "python", "vscode-pylance"],
    "ms-azuretools": "vscode-docker",
    "VisualStudioExptTeam": "vscodeintellicode", 
    "WakaTime": "vscode-wakatime",
    "GitHub": "github-vscode-theme",
    "foxundermoon": "shell-format",
    "donjayamanne": "githistory"
}


def download_ext(_publisher: str, _extension: str) -> None:
    """Download extensions"""
    with Client(
        base_url="https://marketplace.visualstudio.com",
        http2=True,
        follow_redirects=True,
        timeout=None
    ) as conn:
        response = conn.get(
            "/items", params={"itemName": _publisher + "." + _extension}
        )
        tree: html.HtmlElement = html.fromstring(response.content)
        json_content = loads(tree.find('.//div[@class="rhs-content"]/script').text)
        version = json_content["Resources"]["Version"]
        print(_publisher, _extension, version)

        with open(
            f"{os.getenv('HOME')}/extensions/{_publisher.lower()}-{_extension.lower()}.vsix",
            "wb",
        ) as data:
            data.write(
                conn.get(
                    f"/_apis/public/gallery/publishers/{_publisher}/vsextensions/{_extension}/{version}/vspackage"
                ).content
            )


for publisher, extension in extensions.items():
    if isinstance(extension, list):
        for ext in extension:
            download_ext(publisher, ext)
    else:
        download_ext(publisher, extension)
