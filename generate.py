"""
Builds dark_mode.svg and light_mode.svg: an ASCII portrait on the left and a
neofetch-style info panel on the right. GitHub stats are fetched live when a
token is available (GH_TOKEN / GITHUB_TOKEN), otherwise shown as placeholders.

Edit the INFO / CONTACT lists below, then run:  python generate.py
"""
import json, os, urllib.request
from datetime import datetime, timezone
from xml.sax.saxutils import escape

USERNAME = os.environ.get("GH_USER", "lucasting1220")
HEADER = "lucas@ting"
WIDTH = 58  # characters in the right-hand column

# (key, value) pairs; None = blank spacer line
INFO = [
    ("OS", "macOS"),
    ("Origin", "Taipei, Taiwan -> New York City"),
    ("Host", "NYU Courant"),
    ("Kernel", "Computer Science + Mathematics"),
    ("Research", "VLM Security @ Academia Sinica"),
    None,
    ("Languages.Programming", "Python, SQL"),
    ("Languages.Real", "English, Mandarin"),
    None,
    ("Now.Research", "Attention Tracker -> Multimodal"),
    ("Now.Building", "CV Trading-Card Grader"),
    ("Now.Data", "Relocation Matcher (Databricks)"),
    ("Shipped", "WIP Marketplace, 650+ users"),
    ("Second.Brain", "Obsidian, rendered in 3D"),
]
CONTACT = [
    ("Email", "lucasting1220@gmail.com"),
    ("LinkedIn", "linkedin.com/in/lucasting1220"),
    ("GitHub", USERNAME),
]

THEMES = {
    "dark":  dict(bg="#161b22", text="#c9d1d9", key="#ffa657", value="#a5d6ff",
                  cc="#616e7f", add="#3fb950", dele="#f85149", art="#c9d1d9"),
    "light": dict(bg="#f6f8fa", text="#24292f", key="#953800", value="#0a3069",
                  cc="#c2cfde", add="#1a7f37", dele="#cf222e", art="#24292f"),
}

# ---------------------------------------------------------------- GitHub stats
def gql(query, variables, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        out = json.load(r)
    if "errors" in out:
        raise RuntimeError(out["errors"])
    return out["data"]

def fetch_stats():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token or USERNAME.startswith("YOUR_"):
        return None
    repos, stars, cursor = 0, 0, None
    while True:
        d = gql("""query($u:String!,$c:String){user(login:$u){
            followers{totalCount}
            contributed:repositories(ownerAffiliations:[OWNER,COLLABORATOR,ORGANIZATION_MEMBER]){totalCount}
            contributionsCollection{contributionYears}
            repositories(ownerAffiliations:OWNER,first:100,after:$c){
              totalCount nodes{stargazerCount} pageInfo{hasNextPage endCursor}}}}""",
            {"u": USERNAME, "c": cursor}, token)["user"]
        repos = d["repositories"]["totalCount"]
        stars += sum(n["stargazerCount"] for n in d["repositories"]["nodes"])
        if not d["repositories"]["pageInfo"]["hasNextPage"]:
            break
        cursor = d["repositories"]["pageInfo"]["endCursor"]
    commits = 0
    for y in d["contributionsCollection"]["contributionYears"]:
        c = gql("""query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){
            contributionsCollection(from:$f,to:$t){totalCommitContributions restrictedContributionsCount}}}""",
            {"u": USERNAME, "f": f"{y}-01-01T00:00:00Z", "t": f"{y}-12-31T23:59:59Z"}, token)
        cc = c["user"]["contributionsCollection"]
        commits += cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
    return dict(repos=repos, contributed=d["contributed"]["totalCount"],
                stars=stars, commits=commits, followers=d["followers"]["totalCount"])

# ---------------------------------------------------------------- line layout
# a line is a list of (text, css_class)
def kv(key, value, width=WIDTH):
    used = 2 + len(key) + 1 + len(value)
    dots = " " + "." * max(width - used - 2, 1) + " "
    return [(". ", "cc"), (key, "key"), (":", "text"), (dots, "cc"), (value, "value")]

def pair(k1, v1, k2, v2, extra=None):
    left_w = 34
    left = kv(k1, v1, left_w - (len(extra[0]) if extra else 0))
    if extra:
        left += [(" {", "text"), (extra[1], "key"), (": ", "text"), (extra[2], "value"), ("}", "text")]
    right = kv(k2, v2, WIDTH - left_w - 3 + 2)[1:]  # drop leading ". "
    return left + [(" | ", "text")] + right

def rule(title, top=False):
    label = title if top else f"- {title}"
    return [(label + " ", "text" if not top else "key"),
            ("—" * (WIDTH - len(label) - 1), "text")]

def build_lines(stats):
    s = stats or {}
    f = lambda k: f"{s[k]:,}" if k in s else "--"
    L = [rule(HEADER, top=True)]
    for item in INFO:
        L.append([(". ", "cc")] if item is None else kv(*item))
    L.append([])
    L.append(rule("Contact"))
    L += [kv(*c) for c in CONTACT]
    L.append([])
    L.append(rule("GitHub Stats"))
    L.append(pair("Repos", f("repos"), "Stars", f("stars"),
                  extra=(" {Contributed: " + f("contributed") + "}", "Contributed", f("contributed"))))
    L.append(pair("Commits", f("commits"), "Followers", f("followers")))
    return L

# ---------------------------------------------------------------- SVG
def svg(theme, lines, art):
    t = THEMES[theme]
    lh, fs, top = 20, 16, 30
    rows = max(len(lines), len(art))
    h = top + rows * lh + 10
    css = "".join(f".{k}{{fill:{v}}}" for k, v in
                  dict(key=t["key"], value=t["value"], cc=t["cc"], text=t["text"],
                       add=t["add"], dele=t["dele"]).items())
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" font-family="ConsolasFallback,Consolas,\'SF Mono\',Menlo,\'DejaVu Sans Mono\',monospace" '
           f'width="985px" height="{h}px" font-size="{fs}px">',
           f"<style>@font-face{{src:local('Consolas'),local('Consolas Bold');font-family:'ConsolasFallback';"
           f"font-display:swap;-webkit-size-adjust:109%;size-adjust:109%}}{css}text,tspan{{white-space:pre}}</style>",
           f'<rect width="985px" height="{h}px" fill="{t["bg"]}" rx="15"/>',
           f'<text x="15" y="{top}" fill="{t["art"]}" class="ascii">']
    for i, row in enumerate(art):
        out.append(f'<tspan x="15" y="{top + i*lh}">{escape(row)}</tspan>')
    out.append("</text>")
    out.append(f'<text x="420" y="{top}" fill="{t["text"]}">')
    for i, segs in enumerate(lines):
        if not segs:
            continue
        out.append(f'<tspan x="420" y="{top + i*lh}">' +
                   "".join(f'<tspan class="{c}">{escape(x)}</tspan>' for x, c in segs) + "</tspan>")
    out.append("</text></svg>")
    return "\n".join(out)

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    art = open(os.path.join(here, "ascii.txt"), encoding="utf-8").read().rstrip("\n").split("\n")
    try:
        stats = fetch_stats()
    except Exception as e:
        print("stats fetch failed:", e); stats = None
    lines = build_lines(stats)
    for theme in THEMES:
        with open(os.path.join(here, f"{theme}_mode.svg"), "w", encoding="utf-8") as fh:
            fh.write(svg(theme, lines, art))
    print("built", datetime.now(timezone.utc).isoformat(timespec="seconds"), stats or "(placeholder stats)")
