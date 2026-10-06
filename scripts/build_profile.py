"""Generate the website, Google Sites copy, and GitHub profile from shared facts."""
from __future__ import annotations

import json
import shutil
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "content" / "profile.json"
RESEARCH = ROOT / "content" / "research-evidence.json"
SITE = ROOT / "website"


def link(url: str, label: str, **attrs: str) -> str:
    extra = "".join(f' {k}="{escape(v, quote=True)}"' for k, v in attrs.items())
    return f'<a href="{escape(url, quote=True)}"{extra}>{escape(label)}</a>'


def main() -> None:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    research = json.loads(RESEARCH.read_text(encoding="utf-8"))
    pubs = research["publications"]
    patent = research["patents"][0]
    SITE.mkdir(exist_ok=True)
    (SITE / "downloads").mkdir(exist_ok=True)

    for path in (ROOT / "resumes").glob("*"):
        if path.name in {"Hrudayangam-Mehta-Resume.pdf", "Hrudayangam-Mehta-Resume.docx"}:
            shutil.copy2(path, SITE / "downloads" / path.name.lower())

    social = "\n".join(
        f'<li>{link(x["url"], x["label"])}</li>'
        for x in profile["links"] if x["label"] != "Website"
    )
    author_note = '<p class="note">* Equal contribution.</p>'
    publication_rows = []
    for pub in pubs:
        names = []
        for author in pub["authors"]:
            name = escape(author)
            if author == profile["name"]:
                name = f"<strong>{name}</strong>"
            if author in pub["equal_contribution"]:
                name += "*"
            names.append(name)
        refs = [link(pub["url"], "Paper"), link(pub["pdf"], "PDF")]
        if pub.get("code"):
            refs.append(link(pub["code"], "Code"))
        if pub.get("project"):
            refs.append(link(pub["project"], "Project"))
        alternate = ""
        if pub["id"] == "floorplan-journal-2025":
            alternate = '<p class="note">Additional accepted version: ' + link(
                "https://openreview.net/forum?id=uc6nPEx0M2", "OpenReview"
            ) + ". Venue and year: TBD.</p>"
        summary = {
            "woofs-words-2026": "LLM dialogue, symbolic planning, and verbal explanations for robotic guide-dog assistance.",
            "floorplan-journal-2025": "Floor-plan parsing and navigation action generation with vision-language models; evaluation across map size and task complexity.",
            "antisemitism-emnlp-2025": "Evaluation of eight open-source LLMs on 11,315 annotated posts, comparing prompting, decoding, and generated explanations.",
        }[pub["id"]]
        publication_rows.append(
            f'<li class="publication" id="{escape(pub["id"])}">'
            f'<p class="venue">{escape(pub["venue_short"])}</p>'
            f'<h3>{link(pub["url"], pub["title"])}</h3>'
            f'<p class="authors">{", ".join(names)}</p>'
            f'<p>{escape(summary)}</p>'
            f'<p class="contribution"><strong>Contribution:</strong> {escape(pub["contribution"])}</p>'
            f'<p class="paper-links">{" · ".join(refs)}</p>{alternate}</li>'
        )

    experience = []
    references = [(p["title"], p["url"]) for p in pubs] + [(patent["title"], patent["url"])]
    def experience_bullet(text):
        result = escape(text)
        for title, url in references:
            result = result.replace(escape(title), link(url, title))
        return result
    for item in profile["experience"]:
        bullets = "".join(f"<li>{experience_bullet(b)}</li>" for b in item["bullets"])
        experience.append(
            f'<article class="entry"><h3>{escape(item["title"])}</h3>'
            f'<p>{escape(item["organization"])}</p>'
            f'<p class="meta">{escape(item["dates"])}</p><ul>{bullets}</ul></article>'
        )
    education = []
    for item in profile["education"]:
        education.append(
            f'<article class="entry"><h3>{escape(item["degree"])}</h3>'
            f'<p>{escape(item["institution"])}</p>'
            f'<p class="meta">{escape(item["dates"])}</p>'
            f'<p>{escape(item["detail"])}</p></article>'
        )
    skill_rows = "".join(
        f'<p><strong>{escape(x["label"])}:</strong> {escape(", ".join(x["items"]))}</p>'
        for x in profile["skills"]
    )
    resume_file = "hrudayangam-mehta-resume.pdf"
    # Include a document only once it exists, so intermediate builds have no dead links.
    downloads = []
    for filename, label in [(resume_file, "Resume (PDF)")]:
        if (SITE / "downloads" / filename).exists():
            downloads.append(link("downloads/" + filename, label))
    document_links = " · ".join(downloads)

    content = f'''<section id="about" aria-labelledby="about-heading">
      <h2 id="about-heading">About</h2>
      <p class="intro">{escape(profile["summary"])}</p>
      <p>{link(profile["lab"]["url"], "iDRAMA Lab")} · {link("https://www.binghamton.edu/", "Binghamton University")}</p>
    </section>
    <section id="publications" aria-labelledby="publications-heading">
      <h2 id="publications-heading">Publications</h2>
      {author_note}
      <ol class="publications">{"".join(publication_rows)}</ol>
    </section>
    <section id="patent" aria-labelledby="patent-heading">
      <h2 id="patent-heading">Patent application</h2>
      <h3>{link(patent["url"], patent["title"])}</h3>
      <p>{escape(", ".join(patent["inventors"]))}</p>
      <p>{escape(patent["recommended_label"])}.</p>
      <p class="meta">Binghamton University · Reference {escape(patent["reference"])}</p>
    </section>
    <section id="experience" aria-labelledby="experience-heading">
      <h2 id="experience-heading">Experience</h2>
      {"".join(experience)}
    </section>
    <section id="education" aria-labelledby="education-heading">
      <h2 id="education-heading">Education</h2>
      {"".join(education)}
    </section>
    <section id="technical-skills" aria-labelledby="skills-heading">
      <h2 id="skills-heading">Technical skills</h2>
      {skill_rows}
    </section>'''
    canonical = next(x["url"] for x in profile["links"] if x["label"] == "Website")
    html = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Hrudayangam Mehta — PhD student at Binghamton University. Computational social science, preference optimization, AI alignment, and model evaluation.">
  <meta name="color-scheme" content="light">
  <meta property="og:title" content="Hrudayangam Mehta">
  <meta property="og:description" content="Research, publications, and CV. PhD student in the iDRAMA Lab at Binghamton University.">
  <meta property="og:type" content="profile">
  <meta property="og:url" content="{escape(canonical, quote=True)}">
  <link rel="canonical" href="{escape(canonical, quote=True)}">
  <link rel="stylesheet" href="style.css">
  <title>Hrudayangam Mehta</title>
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <div class="page">
    <header class="profile">
      <img class="portrait" src="assets/portrait.jpeg" alt="Hrudayangam Mehta" width="136" height="136">
      <h1>Hrudayangam <br>Mehta</h1>
      <p class="role">{escape(profile["headline"])}<br>{escape(profile["affiliation"])}</p>
      <p class="location">{escape(profile["location"])}</p>
      <ul class="social-links" aria-label="Contact and research profiles">{social}</ul>
      <p class="document-links">{document_links}</p>
      <nav aria-label="Sections">
        <a href="#about">About</a>
        <a href="#publications">Publications</a>
        <a href="#patent">Patent application</a>
        <a href="#experience">Experience</a>
        <a href="#education">Education</a>
      </nav>
    </header>
    <main id="main" tabindex="-1">
      {content}
      <footer><p>Updated October 2026 · {link("mailto:" + profile["email"], profile["email"])}</p></footer>
    </main>
  </div>
</body>
</html>
'''
    (SITE / "index.html").write_text(html, encoding="utf-8")
    # This copy has exactly the same content. Copy rendered sections into Google Sites.
    # It is a handoff artifact, not an automatic Google Sites publication.
    handoff = ROOT / "handoff"
    handoff.mkdir(exist_ok=True)
    embedded_css = (SITE / "style.css").read_text(encoding="utf-8")
    google_html = html.replace('<link rel="stylesheet" href="style.css">', f"<style>{embedded_css}</style>")
    google_html = google_html.replace('src="assets/portrait.jpeg"', 'src="../website/assets/portrait.jpeg"')
    google_html = google_html.replace('href="downloads/', 'href="../website/downloads/')
    (handoff / "google-sites-content.html").write_text(google_html, encoding="utf-8")

    # Use relative documents because this repository contains the generated files.
    md = [f'# {profile["name"]}', '', profile["summary"], '']
    md.append(' · '.join(f'[{x["label"]}]({x["url"]})' for x in profile["links"]))
    md += ['', '[Resume](resumes/Hrudayangam-Mehta-Resume.pdf) · [LaTeX source](resumes/Hrudayangam-Mehta-Resume.tex)', '', '## Research', '',
           '- VLM video annotation for computational social science on social media (ongoing)', '- Preference optimization and VLM alignment',
           '- Language-model evaluation and vision-language reasoning', '', '## Publications', '', '\\* Equal contribution.', '']
    for pub in pubs:
        authors = ', '.join(a + ('\\*' if a in pub['equal_contribution'] else '') for a in pub['authors'])
        md += [f'**[{pub["title"]}]({pub["url"]})**  ', f'{authors}  ', f'{pub["venue_short"]}.', '', pub["contribution"], '']
        refs = []
        if pub.get('code'):
            refs.append(f'[Code]({pub["code"]})')
        if pub.get('project'):
            refs.append(f'[Project]({pub["project"]})')
        if refs:
            md += [' · '.join(refs), '']
        if pub['id'] == 'floorplan-journal-2025':
            md += ['[Additional accepted version on OpenReview](https://openreview.net/forum?id=uc6nPEx0M2) — venue and year: TBD.', '']
    md += ['## Patent application', '', f'**[{patent["title"]}]({patent["url"]})**  ',
           ', '.join(patent['inventors']) + '  ', patent['recommended_label'] + '.', '',
           '## Education', '']
    for edu in profile['education']:
        md.append(f'- **{edu["degree"]}**, {edu["institution"]} — {edu["dates"]}.')
    md += ['', '## Technical skills', '']
    for skill in profile['skills']:
        md.append(f'- **{skill["label"]}:** {", ".join(skill["items"])}.')
    md = [line[:-2] + '<br>' if line.endswith('  ') else line for line in md]
    (ROOT / 'README.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('Generated website/index.html, README.md, and handoff/google-sites-content.html.')


if __name__ == '__main__':
    main()
