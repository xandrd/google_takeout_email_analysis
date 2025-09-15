import json
import pickle
from collections import defaultdict
from email.utils import getaddresses
from email.header import decode_header

def decode_header_to_str(value: str) -> str:
    if not value:
        return ""
    parts = []
    for bytestr, enc in decode_header(value):
        parts.append(bytestr.decode(enc or "utf-8", errors="replace") if isinstance(bytestr, bytes) else bytestr)
    return "".join(parts)

def address_pairs(header_val: str):
    if not header_val:
        return []
    decoded = decode_header_to_str(header_val)
    return [(n.strip(), a.lower()) for n, a in getaddresses([decoded]) if a]

def normalize_name(name: str) -> str:
    if not name:
        return ""
    # remove quotes and trim
    name = name.strip().strip("'").strip('"')
    # handle "Last, First" → "First Last"
    if "," in name:
        parts = [p.strip() for p in name.split(",")]
        if len(parts) == 2:
            name = f"{parts[1]} {parts[0]}"
    # title-case (Anthony Saikin, John A Doe)
    return " ".join(w.capitalize() for w in name.split())

# ----------------- load headers -----------------
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

cache_header_path = config["mbox_cache_headers_path2"]
cache_adress_book_path = config["mbox_cache_address_book2"]

with open(cache_header_path, "rb") as fh:
    msg_headers = pickle.load(fh)   # {msg_id: {header_name: header_value}}

# ----------------- build address book -----------------
address_book = defaultdict(set)

for hdrs in msg_headers.values():
    for h in ("From", "To", "Cc", "Reply-To", "Sender"):
        if h in hdrs:
            for name, email in address_pairs(hdrs[h]):
                if email and name and email.lower() != name.lower() and "@" not in name:
                    address_book[email].add(normalize_name(name))

# ----------------- example preview -----------------
for email, names in list(address_book.items())[:10]:
    print(email, names)


with open(cache_adress_book_path, "wb") as fh:
    pickle.dump(address_book, fh, protocol=pickle.HIGHEST_PROTOCOL)