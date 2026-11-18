
from datasets import load_dataset
import pandas as pd
from pathlib import Path

print("Downloading SpamAssassin dataset...")

dataset = load_dataset(
    "talby/spamassassin",
    "text",
    split="train"
)

print("Dataset downloaded successfully!")

df = dataset.to_pandas()

# Convert numerical class labels into readable labels
label_names = dataset.features["label"].names

df["label"] = df["label"].apply(
    lambda x: label_names[int(x)]
)

df = df[["text", "label"]].dropna()

df["text"] = df["text"].astype(str).str.strip()
df["label"] = df["label"].str.lower()

df = df[df["label"].isin(["spam", "ham"])]
df = df[df["text"].str.len() > 10]
df = df.drop_duplicates(subset=["text"])

output = Path("data/emails.csv")
output.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(output, index=False)

print("\n========== DATASET SUMMARY ==========")
print("Total emails:", len(df))
print("\nEmail distribution:")
print(df["label"].value_counts())

print("\nDataset saved successfully at:", output)
