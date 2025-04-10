
import pandas as pd

def optimize_allocation(df, total_capital=1_000_000, max_weight=0.30):
    if "final_score" not in df.columns or df.empty:
        return df
    df = df.copy()
    df["Weight"] = df["final_score"] / df["final_score"].sum()
    df["Weight"] = df["Weight"].apply(lambda w: min(w, max_weight))
    df["Weight"] = df["Weight"] / df["Weight"].sum()
    df["Allocation"] = df["Weight"] * total_capital
    return df
