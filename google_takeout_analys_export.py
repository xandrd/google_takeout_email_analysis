import pandas as pd
import json
import pickle
from pathlib import Path


with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

cache_adress_book_path = config["mbox_cache_address_book2"]
cache_counter_path = config["mbox_cache_counter_path2"]
excel_path = config["excel_path2"]

with open(cache_adress_book_path, "rb") as fh:
    address_book = pickle.load(fh)

with open(cache_counter_path, "rb") as fh:
    data = pickle.load(fh)

all_replies = data["all_replies"]
one_replies = data["one_replies"]
small_replies = data["small_replies"]
group_replies = data["group_replies"]

# assume these exist from earlier steps
# address_book: dict[email] -> set(names)
# all_replies: Counter with counts per email

rows = []
for email, names in address_book.items():
    count = all_replies.get(email, 0)
    count_one = one_replies.get(email, 0)
    count_small = small_replies.get(email, 0)
    count_group = group_replies.get(email, 0)

    if "@" in email:
        domain = email.split("@", 1)[1].lower()        # epss.ucla.edu
        host = ".".join(domain.split(".")[-2:])        # ucla.edu
    else:
        domain, host = "", ""

    # turn the set of names into a sorted list for stable columns
    name_list = sorted(names)

    row = {
        "count": count,
        "one": count_one,
        "small": count_small,
        "group": count_group,
        "email": email,
        "email-domain": domain,
        "email-host": host,
    }

    # expand names into columns: name1, name2, ...
    for i, n in enumerate(name_list, start=1):
        row[f"name{i}"] = n

    rows.append(row)

# build DataFrame
df = pd.DataFrame(rows)

# optional: sort by count, descending
df = df.sort_values(by="count", ascending=False)

# save to Excel
out_path = Path(excel_path)
df.to_excel(out_path, index=False)

print(f"✅ Exported {len(df)} rows to {out_path}")

