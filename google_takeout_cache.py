# Create cache from mbox file (not content - pickle file)
import json
import mailbox
import pickle
from email.utils import parseaddr, getaddresses
from email.header import decode_header

# ---------- Helpers ----------
def decode_header_to_str(value: str) -> str:
    """Decode RFC2047 headers to plain UTF-8."""
    if not value:
        return ""
    parts = []
    for bytestr, enc in decode_header(value):
        if isinstance(bytestr, bytes):
            parts.append(bytestr.decode(enc or "utf-8", errors="replace"))
        else:
            parts.append(bytestr)
    return "".join(parts).strip()

def normalize_from(from_header: str) -> str:
    """Return only the plain email from From header (lowercased)."""
    _, email = parseaddr(from_header or "")
    return email.lower()

def filter_my_addresses(addr_header: str, my_addrs: set[str]) -> list[str]:
    """Return only user's own addresses that appear in To/Cc (lowercased)."""
    if not addr_header:
        return []
    addrs = [a.lower() for _, a in getaddresses([addr_header])]
    return [a for a in addrs if a in my_addrs]

def parse_all_addresses(header_value: str) -> list[str]:
    """Return ALL addresses (lowercased) from a To/Cc/Bcc-like header."""
    if not header_value:
        return []
    return [addr.lower() for _, addr in getaddresses([header_value])]

def split_labels(x: str) -> list[str]:
    """Parse Gmail Takeout 'X-Gmail-Labels' into a clean list."""
    if not x:
        return []
    return [s.strip() for s in x.split(",") if s.strip()]

def summarize_mime(msg) -> tuple[bool, list[str]]:
    """
    Return (has_attachments, unique_content_types).
    Walk parts WITHOUT decoding payloads.
    """
    has_attach = False
    ctypes = set()

    if msg.is_multipart():
        for part in msg.walk():
            # Skip the container itself if desired
            ctype = part.get_content_type()
            cdisp = (part.get("Content-Disposition") or "").lower()
            if "attachment" in cdisp:
                has_attach = True
            ctypes.add(ctype)
    else:
        ctypes.add(msg.get_content_type())

    return has_attach, sorted(ctypes)



# ---------- Load config & MBOX ----------
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

mbox_path = config["mbox_path2"]
cache_path = config.get("mbox_cache_path2", "cache.pkl")
cache_header_path = config.get("mbox_cache_headers_path2", "cache.pkl")
#my_addresses = set(a.lower() for a in config("my_addresses"))

# Read the data
mbox = mailbox.mbox(mbox_path)

# ---------- Build lightweight cache (headers only) ----------
summary = {}  # id -> dict(from, to, title, date, msgid, labels, has_attachments, content_types, cc_my)
msg_headers = {}  # id -> all raw headers
for idx, msg in enumerate(mbox):

    # Raw headers go into separate dict
    msg_headers[idx] = {k: v for (k, v) in msg.items()}


    item = {
        "From": normalize_from(msg.get("From", "")),
        "To": parse_all_addresses(msg.get("To", "")),                                   # only your addresses
        "CC": parse_all_addresses(msg.get("Cc", "")),
        "Title": decode_header_to_str(msg.get("Subject", "")),
        "Date": decode_header_to_str(msg.get("Date", "")),
        "Message-ID": decode_header_to_str(msg.get("Message-ID", "")),
        "In-Reply-To": decode_header_to_str(msg.get("In-Reply-To", "")),
        "References": decode_header_to_str(msg.get("References", "")),
        "Labels": split_labels(msg.get("X-Gmail-Labels", "")),
    }

    # MIME summary (no bodies, no decoding)
    has_attach, ctypes = summarize_mime(msg)
    item["HasAttachments"] = has_attach
    item["ContentTypes"] = ctypes

    summary[idx] = item

# ---------- Persist cache ----------
with open(cache_path, "wb") as fh:
    pickle.dump(summary, fh, protocol=pickle.HIGHEST_PROTOCOL)

# ---------- Persist cache ----------
with open(cache_header_path, "wb") as fh:
    pickle.dump(msg_headers, fh, protocol=pickle.HIGHEST_PROTOCOL)

print(f"✅ Cached {len(summary)} messages from: {mbox_path}")
print(f"🧊 Pickle saved to: {cache_path}")
