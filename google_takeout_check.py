import mailbox
import json
from collections import Counter
from email.header import decode_header

# Load config
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

# Path to your Takeout file
mbox_path = config["mbox_path"]
mbox = mailbox.mbox(mbox_path)

domains = Counter()

label_counts = Counter()
total = len(mbox)


for i, msg in enumerate(mbox, start=1):
    labels_raw = msg.get('X-Gmail-Labels', '')
    if labels_raw:

        decoded_labels = decode_header(labels_raw)
        decoded = ''.join(
            part.decode(enc or 'utf-8') if isinstance(part, bytes) else part
            for part, enc in decoded_labels
        )
        labels = [label.strip() for label in decoded.split(",")]

        label_counts.update(labels)

    # Print progress every 50 messages (tune as needed)
    if i % 50 == 0 or i == total:
        print(f"Processed {i}/{total} messages...")

print("\nLabel counts:\n")
for label, count in label_counts.most_common():
    print(f"{label:20} {count}")
