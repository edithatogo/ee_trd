"""
Tornado plot from dsa_results.csv
- Plots absolute impact on incremental NMB (AUD) for Low and High values per parameter.
"""
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("dsa_results.csv")
df["MaxImpact"] = df[["Impact_low","Impact_high"]].max(axis=1)
df = df.sort_values("MaxImpact", ascending=True)

y = range(len(df))
labels = df["Parameter"].tolist()

fig, ax = plt.subplots(figsize=(8, max(4, 0.35*len(df))))
ax.barh(y, df["Impact_high"], left=0)
ax.barh(y, -df["Impact_low"], left=0)
ax.set_yticks(y)
ax.set_yticklabels(labels)
ax.set_xlabel("Impact on Incremental NMB (AUD)")
ax.set_title("One-way DSA Tornado Plot (Ketamine vs ECT)")
fig.tight_layout()
fig.savefig("tornado_plot.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print("Saved tornado_plot.png")
