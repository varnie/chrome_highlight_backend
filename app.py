import logging

import spacy
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from spacy.cli import download
from spacy.util import is_package

PERSONS_HIGHLIGHT_COLOR = "#ffff00"  # yellow
LOCATIONS_HIGHLIGHT_COLOR = "#00ffff"  # aqua
ORGANIZATIONS_HIGHLIGHT_COLOR = "#ff00ff"  # magenta

ALLOWED_TAGS = {'p', 'div', 'h1', 'h2', 'h3', 'h4', 'span', "td", 'header', "a", "b", "strong", "i", "em", "mark",
                "small", "del", "ins", "sub", "sup"}
EXCLUDED_TAGS = {'script', 'style', 'iframe', 'img'}


def is_textual_tag(tag):
    """Check if tag is textual and should be included in output"""
    return tag.name in ALLOWED_TAGS


def highlight_matches(src, labels):
    color = ''
    matched = False

    if src in labels["persons"]:
        color = PERSONS_HIGHLIGHT_COLOR
        matched = True
    elif src in labels["locs"]:
        color = LOCATIONS_HIGHLIGHT_COLOR
        matched = True
    elif src in labels["orgs"]:
        color = ORGANIZATIONS_HIGHLIGHT_COLOR
        matched = True

    if matched:
        return f'<span style="background-color: {color};">{src}</span>'
    else:
        return None


if not is_package("en_core_web_sm"):
    spacy.cli.download("en_core_web_sm")


def init_app():
    app = Flask(__name__)

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s - %(message)s"))

    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)
    app.logger.info('The server has been started')

    return app


app = init_app()


@app.route('/', methods=['POST'])
def receive_html():
    app.logger.info("receive_html request started")

    data = request.json

    html_content = data.get('pageHtml')
    if not html_content:
        app.logger.error("Bad Request - pageHtml is not provided or empty")
        return 'Bad Request', 400

    soup = BeautifulSoup(html_content, 'html.parser')
    is_valid_html = bool(soup.find())
    if not is_valid_html:
        app.logger.error("Bad Request - non HTML content")
        return 'Bad Request', 400

    text_elements = []
    for tag in soup.find_all(text=True):
        if tag.parent.name not in EXCLUDED_TAGS and is_textual_tag(tag.parent):
            text = tag.strip().replace("\n", " ").replace("\r", " ")
            if text:
                text_elements.append(text)
    text = " ".join(text_elements)

    nlp = spacy.load('en_core_web_sm')
    doc = nlp(text)

    labels = dict(
        persons=[],
        locs=[],
        orgs=[]
    )

    # person, location, organization
    for ent in doc.ents:
        #print(ent.label_, " ", ent.text)
        if ent.label_ == "PERSON":
            labels["persons"].append(ent.text)
        elif ent.label_ == "ORG":
            labels["orgs"].append(ent.text)
        elif ent.label_ in ["LOC", "GPE"]:
            labels["locs"].append(ent.text)

    for _, item in enumerate(labels):
        labels[item] = list(set(labels[item]))

    # highlight matches if any found
    modified = False

    if any(labels.values()):
        for tag in soup.find_all(text=True):
            if tag.parent.name not in EXCLUDED_TAGS and is_textual_tag(tag.parent):
                new_str = highlight_matches(tag.strip(), labels)
                if new_str is not None:
                    tag.replace_with(BeautifulSoup(new_str, "html.parser"))
                    modified = True

    modified_html_content = str(soup) if modified else html_content
    app.logger.info("receive_html request completed")
    return jsonify(message='OKAY', data={"modified_html": modified_html_content})


if __name__ == '__main__':
    app.run()
