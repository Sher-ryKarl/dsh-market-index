"""Build a DSH plugin-market index (format 1) from the npm keyword `dsh-plugin`.

Output validates against @deepseek-ai/dsh-plugin-market-index (parseMarketIndex).
Run: python build_index.py [plugin_count]
"""
import calendar
import json
import re
import sys
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "dsh-community-index/1"}
OUT = "market-index.json"
MAX = int(sys.argv[1]) if len(sys.argv) > 1 else 120

CATEGORIES = {
    "capability": {"en": "Model & Runtime", "zh": "模型与运行时"},
    "research": {"en": "Research", "zh": "科研"},
    "coding": {"en": "Coding", "zh": "编码"},
    "context": {"en": "Context & Memory", "zh": "上下文与记忆"},
    "ui": {"en": "Interface", "zh": "界面"},
    "infra": {"en": "Infra & Ops", "zh": "基础设施"},
    "other": {"en": "Other", "zh": "其他"},
}

RULES = [
    ("context", r"memory|context|compact|recall|记忆|上下文"),
    ("research", r"search|paper|arxiv|literature|scholar|zotero|research|论文|文献|科研"),
    ("coding", r"\bgit\b|code|repo|test|debug|lint|代码|仓库"),
    ("ui", r"theme|skin|sidebar|wallpaper|tray|mobile|表情|主题|皮肤|界面|侧边栏"),
    ("capability", r"ssh|docker|proxy|provider|\bllm\b|model|reasoning|token|balance|模型|代理|计费"),
    ("infra", r"cron|backup|sync|monitor|audit|security|log|备份|监控|审计|安全"),
]


def get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def categorize(desc):
    low = (desc or "").lower()
    for cid, pattern in RULES:
        if re.search(pattern, low):
            return cid
    return "other"


def normalize_url(url):
    if not url:
        return None
    url = re.sub(r"^git\+", "", url.strip())
    url = re.sub(r"^git://", "https://", url)
    url = re.sub(r"^ssh://git@github\.com/", "https://github.com/", url)
    url = re.sub(r"^git@github\.com:", "https://github.com/", url)
    if url.endswith(".git"):
        url = url[:-4]
    return url if url.startswith(("http://", "https://")) else None


def epoch(iso):
    try:
        return calendar.timegm(time.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S"))
    except (ValueError, TypeError):
        return 0


def main():
    objects = []
    for offset in (0, 250, 500):
        try:
            page = get(f"https://registry.npmjs.org/-/v1/search?text=keywords:dsh-plugin&size=250&from={offset}")
        except Exception as exc:  # noqa: BLE001
            print(f"search offset {offset} failed: {exc}")
            break
        objects += page.get("objects", [])
        if len(page.get("objects", [])) < 250:
            break
    objects.sort(key=lambda o: o.get("score", {}).get("final", 0), reverse=True)
    print(f"npm hits: {len(objects)}")

    plugins, seen = [], set()
    for obj in objects:
        name = obj["package"]["name"]
        if name in seen:
            continue
        seen.add(name)
        try:
            pack = get("https://registry.npmjs.org/" + urllib.parse.quote(name, safe="@"))
        except Exception:  # noqa: BLE001
            continue
        latest = (pack.get("dist-tags") or {}).get("latest")
        if not latest or latest not in (pack.get("versions") or {}):
            continue
        version = pack["versions"][latest]
        # 市场只安装 bundle；没声明 dsh.bundle 的包放进去点了也会失败
        dsh_field = version.get("dsh")
        if not (isinstance(dsh_field, dict) and dsh_field.get("bundle")):
            continue
        desc = (pack.get("description") or "").strip() or name
        repo_url = normalize_url(
            (version.get("repository") or pack.get("repository") or {}).get("url")
            if isinstance(version.get("repository") or pack.get("repository"), dict) else None
        )
        author = version.get("author") or pack.get("author") or ""
        if isinstance(author, dict):
            author = author.get("name") or ""
        author = (author or "").strip()
        if not author:
            match = re.search(r"github\.com/([^/]+)", repo_url or "")
            author = match.group(1) if match else name.split("/")[0]

        short = name.split("/")[-1]
        keywords = [k for k in (version.get("keywords") or []) if isinstance(k, str)][:8]
        entry = {
            "name": name,
            "title": {"en": short, "zh": short},
            "description": {"en": desc[:300], "zh": desc[:300]},
            "author": author,
            "metadata": {
                "category": categorize(desc),
                "keywords": keywords,
                "sortKeys": {"downloads": obj.get("downloads", {}).get("monthly", 0)},
            },
            "dist-tags": {k: v for k, v in (pack.get("dist-tags") or {}).items() if k in ("latest", "next", "alpha")},
            "versions": [
                {
                    "version": latest,
                    "publishTimestamp": epoch((pack.get("time") or {}).get(latest, "")),
                    "source": {"type": "npm"},
                }
            ],
        }
        engines = (version.get("engines") or {}).get("dsh")
        if engines:
            entry["versions"][0]["engines"] = {"dsh": engines}
        if repo_url:
            entry["repository"] = {"url": repo_url}
        if pack.get("homepage"):
            homepage = normalize_url(pack["homepage"])
            if homepage:
                entry["homepage"] = homepage
        plugins.append(entry)
        if len(plugins) >= MAX:
            break

    doc = {
        "format": 1,
        "title": {"en": "DSH Community Index", "zh": "DSH 社区插件索引"},
        "description": {
            "en": "Auto-generated from the npm keyword dsh-plugin, ranked by popularity.",
            "zh": "从 npm 的 dsh-plugin 关键词自动生成，按流行度排序。",
        },
        "metadata": {
            "categories": {cid: {"title": title} for cid, title in CATEGORIES.items()},
            "sortKeys": {"downloads": {"title": {"en": "Downloads", "zh": "月下载"}, "order": "desc"}},
        },
        "plugins": plugins,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(f"wrote {len(plugins)} plugins -> {OUT}")


if __name__ == "__main__":
    main()
