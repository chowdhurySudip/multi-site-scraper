import pandas as pd

df = pd.read_csv("transcripts.csv")
counts = df["Page"].value_counts()
low_frequency_pages = counts[counts < 10].index.tolist()

print(low_frequency_pages)