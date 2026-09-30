import urllib.request
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-ecdb51b92176"

ALL_ROLES = ["Product Designer", "Design Engineer", "PM", "Frontend", "Backend", "FDE"]

SOURCES = [
    # General Tech & Industry News (breaking news, launches, AI releases)
    {
        "name": "Hacker News",
        "url": "https://hacker-news.firebaseio.com/v0",
        "type": "hackernews",
        "category": "news",
        "roles": ALL_ROLES,  # Available to all roles
    },
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "type": "rss",
        "category": "news",
        "roles": ALL_ROLES,
    },
    {
        "name": "The Verge",
        "url": "https://www.theverge.com/rss/index.xml",
        "type": "rss",
        "category": "news",
        "roles": ALL_ROLES,
    },
    {
        "name": "Product Hunt",
        "url": "https://www.producthunt.com/feed",
        "type": "rss",
        "category": "news",
        "roles": ["PM", "Product Designer", "Design Engineer", "Frontend"],
    },
    {
        "name": "GitHub Blog",
        "url": "https://github.blog/feed/",
        "type": "rss",
        "category": "news",
        "roles": ["Frontend", "Backend", "Design Engineer", "FDE"],
    },
    {
        "name": "Figma Blog",
        "url": "https://www.figma.com/blog/feed/atom.xml",
        "type": "rss",
        "category": "news",
        "roles": ["Product Designer", "Design Engineer", "Frontend"],
    },
    {
        "name": "Figma Releases",
        "url": "https://releases.figma.com/feed",
        "type": "rss",
        "category": "news",
        "roles": ["Product Designer", "Design Engineer", "Frontend"],
    },
    # Reads / In-depth essays & analyses
    {
        "name": "Smashing Magazine",
        "url": "https://www.smashingmagazine.com/feed/",
        "type": "rss",
        "category": "reads",
        "roles": ["Product Designer", "Design Engineer", "Frontend"],
    },
    {
        "name": "CSS-Tricks",
        "url": "https://css-tricks.com/feed/",
        "type": "rss",
        "category": "reads",
        "roles": ["Frontend", "Design Engineer"],
    },
    {
        "name": "Sidebar IO",
        "url": "https://sidebar.io/feed.xml",
        "type": "rss",
        "category": "reads",
        "roles": ["Product Designer", "Design Engineer"],
    },
    {
        "name": "UX Collective",
        "url": "https://uxdesign.cc/feed",
        "type": "rss",
        "category": "reads",
        "roles": ["Product Designer"],
    },
    {
        "name": "A List Apart",
        "url": "https://alistapart.com/main/feed/",
        "type": "rss",
        "category": "reads",
        "roles": ["Product Designer", "Design Engineer", "Frontend"],
    },
    {
        "name": "Lenny's Newsletter",
        "url": "https://www.lennysnewsletter.com/feed",
        "type": "rss",
        "category": "reads",
        "roles": ["PM"],
    },
    {
        "name": "Department of Product",
        "url": "https://www.departmentofproduct.com/feed/",
        "type": "rss",
        "category": "reads",
        "roles": ["PM"],
    },
    {
        "name": "The Pragmatic Engineer",
        "url": "https://blog.pragmaticengineer.com/rss/",
        "type": "rss",
        "category": "reads",
        "roles": ["Backend", "Frontend", "FDE", "PM"],
    },
    {
        "name": "InfoQ",
        "url": "https://feed.infoq.com/",
        "type": "rss",
        "category": "reads",
        "roles": ["Backend", "FDE"],
    },
    {
        "name": "Lobsters",
        "url": "https://lobste.rs/rss",
        "type": "rss",
        "category": "reads",
        "roles": ["Backend", "Frontend", "FDE"],
    },
]


def test_url(url: str, source_type: str) -> bool:
    target = url
    if source_type == "hackernews":
        target = f"{url}/topstories.json"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Loopy/1.0)"}
    try:
        req = urllib.request.Request(target, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Error checking {url}: {e}")
        return False


def seed():
    print(f"Connecting to Firestore for project {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)
    collection = db.collection("sources")

    seeded_count = 0
    for src in SOURCES:
        name = src["name"]
        url = src["url"]
        stype = src["type"]
        category = src["category"]
        roles = src["roles"]

        print(f"Testing {name} ({url})...")
        if not test_url(url, stype):
            print(f"  [SKIPPED] {name} failed connectivity check.")
            continue

        doc_id = name.lower().replace(" ", "_").replace("'", "").replace("-", "_")
        doc_ref = collection.document(doc_id)
        doc_ref.set({
            "name": name,
            "url": url,
            "type": stype,
            "category": category,
            "roles": roles,
        })
        print(f"  [SEEDED] {name} [{category}] -> roles: {roles}")
        seeded_count += 1

    print(f"\nSuccessfully seeded {seeded_count} sources into Firestore 'sources' collection.")


if __name__ == "__main__":
    seed()
