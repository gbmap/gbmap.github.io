
import os
from io import StringIO, BytesIO
import glob
import markdown
from bs4 import BeautifulSoup


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


def generate_preview(html: str) -> str:
    # search for media in html (img, video, iframe)
    # set the media float and take all space from parent
    soup = BeautifulSoup(html, 'html.parser')

    # Find all media tags
    media_tags = soup.find_all(['img', 'video', 'iframe'])
    classes = {
        'img': 'img-preview',
        'video': 'video-preview',
        'iframe': 'iframe-preview'
    }

    # create preview
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

    soup.append(content_wrapper)
    soup.append(media_container)

    # Return the modified HTML as a string
    return str(soup).replace("&amp;", "&")

def main():
    CONTENT_TAG = "%%CONTENT%%"
    PAGES_DIR = "./pages"
    pages = list(filter(lambda f: os.path.isdir(f), glob.glob(f"{PAGES_DIR}/*")))
    print(list(pages))

    with open("_template.html", "r") as f:
        html_boiler_plate = f.read()

    with open("_item_template.html", "r") as f:
        html_item = f.read()

    for page in pages:
        files = glob.glob(os.path.join(page, "*"))
        html_items = []
        for file in files:
            with open(file, "r") as f:
                md_html = markdown.markdown(f.read())
            html_items.append(html_item.replace(CONTENT_TAG, generate_preview(md_html)))

        html_page = html_boiler_plate.replace(CONTENT_TAG, '\n'.join(html_items))
        page_fname = f"{os.path.basename(page)}.html"
        with open(page_fname, "w") as f:
            f.write(html_page)


if __name__ == "__main__":
    main()