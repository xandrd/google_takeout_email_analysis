import json
import pickle
from collections import defaultdict
from collections import Counter


with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

cache_path = config["mbox_cache_path2"]
cache_header_path = config["mbox_cache_headers_path2"]
cache_counter_path = config["mbox_cache_counter_path2"]


with open(cache_path, "rb") as fh:
    summary = pickle.load(fh)

print(f"✅ Loaded {len(summary)} messages from cache")


labels_count = defaultdict(int)
for m in summary.values():
    for l in m["Labels"]:
        labels_count[l] += 1

for key, val in sorted(labels_count.items(), key=lambda x: -x[1]):
    print(key, val)


one_replies = Counter()
small_replies = Counter()
group_replies = Counter()

for m in summary.values():
    if "out of office" in m["Title"].lower():
        continue

    if "Sent" not in m["Labels"]:
        continue

    To = m["To"]
    len_to = len(To)

    if len_to == 1:
        one_replies.update([To[0]])
        continue

    if len_to < 10:
        for t in To:
            small_replies.update([t])
        continue

    for t in To:
        group_replies.update([t])
        continue

all_replies = Counter()
all_replies = one_replies + small_replies + group_replies

print(len(one_replies), len(small_replies), len(group_replies))

import pickle

data = {
    "all_replies": all_replies,
    "one_replies": one_replies,
    "small_replies": small_replies,
    "group_replies": group_replies,
}

with open(cache_counter_path, "wb") as f:
    pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
