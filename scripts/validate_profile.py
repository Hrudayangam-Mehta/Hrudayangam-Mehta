"""Check factual consistency, publication links, and case-sensitive local website paths."""
import json
import re
import html as html_module
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.main = False
        self.main_text = []
        self.links = []
        self.ids = set()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append(tag)
        if tag == "main":
            self.main = True
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for attribute in ("href", "src"):
            if attribute in attrs:
                self.links.append(attrs[attribute])

    def handle_endtag(self, tag):
        if tag == "main":
            self.main = False

    def handle_data(self, text):
        if self.main:
            self.main_text.append(text)


def parse(path):
    doc = Document()
    text = path.read_text(encoding="utf-8")
    doc.feed(text)
    return doc, text


def main():
    site, html = parse(ROOT / "website/index.html")
    google, _ = parse(ROOT / "handoff/google-sites-content.html")
    assert site.main_text == google.main_text, "Google Sites copy differs from website"
    assert "table" not in site.tags, "Unexpected table layout"
    assert "script" not in site.tags, "Unexpected JavaScript dependency"
    assert not re.search(r"preprint|arxiv\.org|Hire Me|quick learner", html, re.I)
    assert "Hrudayangam <br>Mehta" in html, "Name must retain a space at mobile width"
    for value in site.links:
        parsed = urlparse(value)
        if parsed.scheme:
            continue
        if parsed.fragment:
            assert parsed.fragment in site.ids, value
        if not parsed.path:
            continue
        current = ROOT / "website"
        for part in Path(unquote(parsed.path)).parts:
            assert part in {p.name for p in current.iterdir()}, f"Missing or incorrect case: {value}"
            current /= part
        assert current.is_file(), value
    profile = json.loads((ROOT / "content/profile.json").read_text(encoding="utf-8"))
    research = json.loads((ROOT / "content/research-evidence.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for publication in research["publications"]:
        assert publication["url"] in site.links
        assert publication["url"] in readme
        assert publication["status"] == "published"
        assert publication["contribution"] in html_module.unescape(html)
        assert publication["contribution"] in readme
    for degree in profile["education"]:
        assert degree["dates"] in html and degree["dates"] in readme
    assert "63/884,317" in html and "63/884,317" in readme
    assert "provisional patent application" in html
    articles = re.findall(r'<article class="entry">(.*?)</article>', html, re.S)
    current_ra = next(a for a in articles if "iDRAMA Lab" in a and "Research Assistant" in a)
    air_ra = next(a for a in articles if "AIR" in a and "Graduate Research Assistant" in a)
    assert "63/884,317" in current_ra and "From Woofs to Words" in current_ra
    assert "May 2024 - Present" in current_ra and "TBD" not in current_ra
    assert "VLM" in current_ra and "alignment" in current_ra and "social-media videos" in current_ra
    assert (ROOT / "resumes/Hrudayangam-Mehta-Resume.pdf").read_bytes() == (ROOT / "website/downloads/hrudayangam-mehta-resume.pdf").read_bytes(), "Website resume download is stale"
    assert "Aug 2023 - May 2024" in air_ra
    assert "Vision language models can parse floor plan maps" in air_ra
    assert "https://www.elspub.com/doi/10.55092/rl20250011" in air_ra
    assert any("iSmriti" in a for a in articles), "iSmriti must remain on the website"
    assert not any("anthology" in p.name.lower() for p in (ROOT / "website").rglob("*"))
    print("PASS: shared content, all three publications, degree dates, provisional patent, and case-sensitive local links.")
    print("PASS: no table layout, preprint links, placeholder actions, or application-only CV in public website output.")
    print("PASS: iDRAMA/AIR dates, current VLM research, publication contributions, website resume download, and website-only iSmriti.")


if __name__ == "__main__":
    main()
