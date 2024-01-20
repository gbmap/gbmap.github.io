
import os
from io import StringIO, BytesIO
import glob
from typing import Iterable, Tuple
import json
import random
import requests
import markdown
from urllib.parse import urljoin
from bs4 import BeautifulSoup

CONTENT_TAG = "%%CONTENT%%"
PAGES_DIR = "./pages"
GH_PROFILE = "https://github.com/gbmap"
GH_REPOS = [
    ("poormans-weather-station", "main"), ("AgentBasedMapGenerator", "master"), ("pytorch_dcgan", "main"), ("pytorch_style_transfer", "main")
]
GH_SHADERS_REPO = "https://github.com/gbmap/glsl-sandbox"
GH_SHADERS_BRANCH = "main"
GH_SHADERS_VIDEOS = "videos"
GH_SHADERS_SRC = "src"

def handle_media_tag(tag):
    if tag.name == 'video':
        # Set autoplay to True and remove controls
        if 'controls' in tag.attrs:
            del tag['controls']
        tag['autoplay'] = None
        tag['muted'] = None
        tag['loop'] = None
    elif tag.name == 'iframe':
        # If the iframe is an embedded video from YouTube, mute it, set to autoplay and hide controls
        if 'youtube.com' in tag['src']:
            tag['src'] += "?autoplay=1&mute=1&controls=0"

    elif tag.name == "img":
        tag['style'] = None


def generate_preview(html: str, href: str = None) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    media_tags = soup.find_all(['img', 'video', 'iframe'])

    if len(media_tags) == 0:
        colors = ["red", "blue", "green", "yellow", "purple"]  # Replace with your colors
        color = random.choice(colors)
        div = soup.new_tag('div')
        div['class'] = 'media-container'
        div['style'] = f'background-color: {color};'
        media_tags.append(div)
 
    # create preview
    if len(media_tags) > 0:
        media_tag = media_tags[0]
        media_container = soup.new_tag('div')
        media_container['class'] = 'media-container'
        media_tag.wrap(media_container)
        media_tag['class'] = 'media'
        handle_media_tag(media_tag)

        other_tags = [tag for tag in soup.find_all() if tag not in media_container.find_all()]
        content_wrapper = soup.new_tag('div')
        content_wrapper['class'] = 'content-wrapper'
        for tag in other_tags:
            content_wrapper.append(tag.extract())

        # if href:
        #     # push an a element to the content wrapper that fills everything with a redirect link
        #     a = soup.new_tag('a')
        #     a['href'] = href
        #     a['style'] = 'position: absolute; top: 0; right: 0; bottom: 0; left: 0; color: transparent; z-index:10'
        #     soup.append(a)


        soup.append(content_wrapper)
        soup.append(media_container)

    # Return the modified HTML as a string
    return str(soup).replace("&amp;", "&")

def gen_pages(html_item_template: str , pages_folder: str = "./pages") -> Iterable[Tuple[str, Iterable[str]]]:
    pages = list(filter(lambda f: os.path.isdir(f), glob.glob(f"{pages_folder}/*")))
    return [(os.path.basename(page), list(map(lambda s: html_preview_from_markdown(open(s,"r").read(), html_item_template), glob.glob(os.path.join(page, "*"))))) for page in pages]

def gen_repos(html_item_template: str, profile:str = GH_PROFILE, repos: Iterable[str] = GH_REPOS):
    def _repo(repo, branch):
        base_url = f'{profile}/{repo}/raw/{branch}/'
        text = requests.get(base_url + 'README.md').text

        # change it to all tags that have a src attr
        soup = BeautifulSoup(text, 'html.parser')
        for tag in soup.find_all(src=True):
            tag['src'] = urljoin(base_url, tag['src'])

        return str(soup)

    return [html_preview_from_markdown(_repo(repo, branch), html_item_template, f'{profile}/{repo}') for repo, branch in repos]

def gen_shaders(html_item_template: str, shaders_repo: str = GH_SHADERS_REPO, branch: str = GH_SHADERS_BRANCH, videos: str = GH_SHADERS_VIDEOS, src: str = GH_SHADERS_SRC):
    videos_url = f"{shaders_repo}/tree/{branch}/{videos}"
    md_template = """
# {}
<video autoplay class="media" loop muted>
<source src="{}" type="video/{}"/>
</video>
"""
    return [html_preview_from_markdown(md_template.format(os.path.splitext(f['name'])[0], f"{shaders_repo}/raw/{branch}/{f['path']}", os.path.splitext(f['path'])[-1][1:]), html_item_template) for f in json.loads(requests.get(videos_url).text)["payload"]["tree"]["items"]]

def html_preview_from_markdown(f: str, html_template: str, href: str = None) -> str:
    return html_template.replace(CONTENT_TAG, generate_preview(markdown.markdown(f), href),)

def gen_index_preview(html_pages, html_repos):
    prototypes_page = list(filter(lambda t: "prototype" in t[0], html_pages))[0][1]
    return  prototypes_page + html_repos


def main():
    html_boiler_plate = open("_template.html", "r").read()
    html_item = open("_item_template.html", "r").read()


    html_pages = gen_pages(html_item)
    _=[open(f"{page}.html", "w").write(html_boiler_plate.replace(CONTENT_TAG, '\n'.join(htmls))) for page, htmls in html_pages]

    html_repos = gen_repos(html_item)
    open(f"repos.html", "w").write(html_boiler_plate.replace(CONTENT_TAG, '\n'.join(html_repos)))
    open(f"shaders.html", "w").write(html_boiler_plate.replace(CONTENT_TAG, '\n'.join(gen_shaders(html_item))))
    open(f"index_previews.html", "w").write(html_boiler_plate.replace(CONTENT_TAG, '\n'.join(gen_index_preview(html_pages, html_repos))))



if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("-c", "--clear", action="store_true")

    args = parser.parse_args()
    if args.clear:
        _=list(map(os.remove,list(filter(lambda f: not os.path.basename(f).startswith("_"), glob.glob("*.html")))))
    else:
        main()