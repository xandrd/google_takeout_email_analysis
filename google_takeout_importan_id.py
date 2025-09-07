import mailbox
import code
import json
from email.utils import parseaddr, getaddresses
from collections import defaultdict
from email.header import decode_header

# --- Load config ---
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

mbox_path = config["mbox_path"]
my_addresses = {addr.lower() for addr in config["my_addresses"]}


def normalize_from(from_header):
    """Return only the plain email from From header."""
    if isinstance(from_header, str) :
        _, email = parseaddr(from_header or "")
    else:
        _, email = parseaddr(str(from_header) or "")

    return email.lower()

def normalize_to(to_header):
    """Return only your addresses from To header (if any)."""
    if to_header:
        all_addrs = [addr.lower() for _, addr in getaddresses([to_header])]
        return [addr for addr in all_addrs if addr in my_addresses]
    return ""

def normalize_subject(subj):
    if isinstance(subj, str):
        return subj.strip()
    else:  # it's a Header object
        decoded_parts = decode_header(str(subj))
        return ''.join(
            part.decode(enc or 'utf-8') if isinstance(part, bytes) else part
            for part, enc in decoded_parts
        ).strip()

mbox = mailbox.mbox(mbox_path)

important_unread = {}  # key = msg index, value = labels list

for i, msg in enumerate(mbox, start=1):
    labels_raw = msg.get('X-Gmail-Labels', '') or ''
    decoded_labels = decode_header(labels_raw)
    decoded = ''.join(
        part.decode(enc or 'utf-8') if isinstance(part, bytes) else part
        for part, enc in decoded_labels
    )
    labels = [label.strip() for label in decoded.split(",")]

    if "Important" in labels and "Unread" in labels:
        important_unread[i] = labels

    if i % 1000 == 0:
        print(f"Processed {i} messages... matched {len(important_unread)}")


# assume important_unread2 is already built (dict of ID -> labels)
summary = {}
for idx in important_unread.keys():
    msg = mbox[idx]
    print(idx)
    summary[idx] = {
        "From": normalize_from(msg.get("From")),
        "To": normalize_to(msg.get("To")),
        "Title": msg.get("Subject", ""),
        "Labels": important_unread[idx]
    }

# Group by domain
by_domain = defaultdict(list)

for idx, data in summary.items():
    email = data["From"]
    if not email or "@" not in email:
        continue
    domain = email.split("@")[-1].lower()
    by_domain[domain].append((idx, data))

# Sort: first by length (descending), then by domain
sorted_domains = sorted(
    by_domain.items(),
    key=lambda x: (-len(x[1]), x[0])
)

# Print grouped output
for domain, items in sorted_domains:
    # Sort items within the domain by "From"
    items_sorted = sorted(items, key=lambda x: x[1]["From"].lower())

    print(domain)
    for idx, data in items_sorted:
        print(f"  ID={idx} | From={data['From']} | To={data['To']} | Title={data['Title']}")
    print(f"{domain}: {len(items)}\n\n")

# Print grouped output (only domains with exactly 1 email)
for domain, items in sorted_domains:
    if len(items) == 1:
        items_sorted = sorted(items, key=lambda x: x[1]["From"].lower())

        print(domain)
        # for idx, data in items_sorted:
        #     print(f"  ID={idx} | From={data['From']} | To={data['To']} | Title={data['Title']}")
        # print(f"{domain}: {len(items)}\n\n")

#code.interact(local=locals())