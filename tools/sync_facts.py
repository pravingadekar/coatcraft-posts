"""Snapshot CoatCraft's service/industry facts from the CRM's WhatsApp bot content into brand/facts.json.

The CRM repo is only read. Posts may only claim what is in facts.json.

    python tools/sync_facts.py [path/to/whatsapp-bot-content.php]
"""
import json
import os
import re
import sys

DEFAULT_SRC = r"C:/xampp/htdocs/CoatCraftSolutions/CoatCraftSolutions/whatsapp-bot-content.php"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FIELD = re.compile(r"'([a-z_]+)' => '((?:[^'\\]|\\.)*)'")
LIST = re.compile(r"'([a-z_]+)' => \[([^\]]*)\]")
ENTRY = re.compile(r"'([a-z0-9_]+)' => \[(.*?)\n    \],", re.S)


def block(src, name):
    start = src.index("[", src.index(f"const {name} = ["))
    depth = 0
    for k in range(start, len(src)):
        depth += src[k] == "["
        depth -= src[k] == "]"
        if depth == 0:
            return src[start:k + 1]
    raise ValueError(name)


def entries(body):
    out = {}
    for key, inner in ENTRY.findall(body):
        fields = {f: v.replace("\\'", "'") for f, v in FIELD.findall(inner)}
        lists = {f: re.findall(r"'([a-z0-9_]+)'", v) for f, v in LIST.findall(inner)}
        out[key] = {**fields, **lists}
    return out


def main():
    src_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    with open(src_path, encoding="utf-8") as f:
        src = f.read()
    facts = {
        "brand": "CoatCraft Solutions",
        "tagline": "Strong Floors. Smart Finishes.",
        "phone": "+91 77458 89111",
        "phone_e164": "+917745889111",
        "email": "sales@coatcraftsolutions.com",
        "website": "www.coatcraftsolutions.com",
        "city": "Pune, Maharashtra",
        "coverage": "Pan-India",
        "industries": entries(block(src, "WA_INDUSTRIES")),
        "services": entries(block(src, "WA_SERVICES")),
    }
    with open(os.path.join(ROOT, "brand", "facts.json"), "w", encoding="utf-8") as f:
        json.dump(facts, f, ensure_ascii=False, indent=2)
    print(len(facts["industries"]), "industries,", len(facts["services"]), "services")


if __name__ == "__main__":
    main()
