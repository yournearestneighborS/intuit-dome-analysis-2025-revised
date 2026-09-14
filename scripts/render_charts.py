#!/usr/bin/env python3
"""Render publication-ready charts from the aggregate public CSV files."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
ASSETS = ROOT / "assets"

NAVY = "#0B1F3A"
RED = "#E31937"
BLUE = "#2D7FF9"
SKY = "#89CFF0"
INK = "#172033"
MUTED = "#667085"
GRID = "#D8DEE9"
PAPER = "#F7F9FC"


def money(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:,.0f}"


def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 12,
            "axes.titlesize": 21,
            "axes.titleweight": "bold",
            "axes.labelsize": 12,
            "axes.labelcolor": INK,
            "axes.edgecolor": GRID,
            "axes.facecolor": "white",
            "figure.facecolor": PAPER,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "legend.frameon": False,
            "savefig.facecolor": PAPER,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.18,
        }
    )


def add_title(fig: plt.Figure, title: str, subtitle: str) -> None:
    fig.suptitle(title, x=0.06, y=0.965, ha="left", color=NAVY, fontsize=24, fontweight="bold")
    fig.text(0.06, 0.91, subtitle, ha="left", va="top", color=MUTED, fontsize=12)


def add_source(fig: plt.Figure, text: str = "Source: 2025 Clippers Business Insights challenge dataset; author analysis.") -> None:
    fig.text(0.06, 0.025, text, ha="left", va="bottom", color=MUTED, fontsize=9)


def save(fig: plt.Figure, name: str) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    fig.savefig(ASSETS / name, dpi=200)
    plt.close(fig)


def revenue_mix() -> None:
    frame = pd.read_csv(DATA / "business_vertical_summary.csv").sort_values("net_sales")
    labels = {
        "Food And Beverage": "Food & beverage",
        "Retail": "Retail",
        "Service Items": "Service items",
    }
    colors = [SKY if value == "Service Items" else BLUE if value == "Retail" else RED for value in frame["business_vertical"]]
    fig, ax = plt.subplots(figsize=(11, 6.2))
    fig.subplots_adjust(left=0.22, right=0.93, top=0.78, bottom=0.16)
    add_title(
        fig,
        "Food & beverage supplied 62.8% of net sales",
        "Revenue mix across 31,346 transactions and three home playoff games",
    )
    bars = ax.barh(frame["business_vertical"].map(labels), frame["net_sales"], color=colors, height=0.58)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda value, _: money(value)))
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    total = frame["net_sales"].sum()
    for bar, value in zip(bars, frame["net_sales"]):
        ax.text(
            value + total * 0.012,
            bar.get_y() + bar.get_height() / 2,
            f"{money(value)}  ·  {value / total:.1%}",
            va="center",
            color=INK,
            fontweight="bold",
        )
    ax.set_xlim(0, frame["net_sales"].max() * 1.28)
    add_source(fig)
    save(fig, "revenue_mix.png")


def game_trend() -> None:
    frame = pd.read_csv(DATA / "game_summary.csv")
    labels = frame["game_label"].str.replace(" · ", "\n", regex=False)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.6, 6.5), gridspec_kw={"wspace": 0.28})
    fig.subplots_adjust(left=0.08, right=0.96, top=0.77, bottom=0.18)
    add_title(
        fig,
        "Sales and average transaction value fell each game",
        "Game 6 net sales were 22.8% below Game 3; average transaction value declined 10.6%",
    )
    bars = ax1.bar(labels, frame["net_sales"], color=[NAVY, BLUE, RED], width=0.62)
    ax1.set_title("Net sales", loc="left", fontsize=15, color=INK, pad=12)
    ax1.yaxis.set_major_formatter(mtick.FuncFormatter(lambda value, _: money(value)))
    ax1.grid(axis="y")
    ax1.set_axisbelow(True)
    ax1.spines[["top", "right", "left"]].set_visible(False)
    ax1.tick_params(axis="x", length=0)
    for bar, value in zip(bars, frame["net_sales"]):
        ax1.text(bar.get_x() + bar.get_width() / 2, value + 7000, money(value), ha="center", color=INK, fontweight="bold")
    ax1.set_ylim(0, frame["net_sales"].max() * 1.18)

    ax2.plot(labels, frame["average_transaction_value"], color=RED, linewidth=3, marker="o", markersize=9)
    ax2.fill_between(np.arange(len(frame)), frame["average_transaction_value"], 0, color=RED, alpha=0.08)
    ax2.set_title("Average transaction value", loc="left", fontsize=15, color=INK, pad=12)
    ax2.yaxis.set_major_formatter(mtick.StrMethodFormatter("${x:,.0f}"))
    ax2.grid(axis="y")
    ax2.set_axisbelow(True)
    ax2.spines[["top", "right", "left"]].set_visible(False)
    ax2.tick_params(axis="x", length=0)
    for index, value in enumerate(frame["average_transaction_value"]):
        ax2.text(index, value + 0.65, f"${value:.2f}", ha="center", color=INK, fontweight="bold")
    ax2.set_ylim(0, frame["average_transaction_value"].max() * 1.25)
    add_source(fig)
    save(fig, "game_trend.png")


def timing_relative_to_tipoff() -> None:
    frame = pd.read_csv(DATA / "game_hour_summary.csv")
    frame = frame.loc[frame["relative_hour"].between(-3, 3)]
    colors = {"Game 3 · Apr 24": NAVY, "Game 4 · Apr 26": BLUE, "Game 6 · May 1": RED}
    fig, ax = plt.subplots(figsize=(12, 6.7))
    fig.subplots_adjust(left=0.10, right=0.95, top=0.78, bottom=0.18)
    add_title(
        fig,
        "The final hour before tipoff was the revenue peak in every game",
        "Hourly net sales normalized to each game's scheduled tipoff; shown window contains 98.8% of sales",
    )
    for game, group in frame.groupby("game_label", sort=False):
        ax.plot(
            group["relative_hour"],
            group["net_sales"],
            label=game,
            color=colors[game],
            linewidth=2.8,
            marker="o",
            markersize=6,
        )
    ax.axvspan(-1, 0, color=RED, alpha=0.07)
    ax.axvline(0, color=INK, linestyle="--", linewidth=1.3)
    ax.text(0.04, 0.96, "TIPOFF", transform=ax.get_xaxis_transform(), color=INK, fontsize=10, fontweight="bold", va="top")
    ax.annotate(
        "Revenue peak\nfor all 3 games",
        xy=(-1, frame.loc[frame["relative_hour"] == -1, "net_sales"].max()),
        xytext=(-2.45, 151000),
        arrowprops={"arrowstyle": "->", "color": RED, "lw": 1.5},
        color=RED,
        fontweight="bold",
    )
    ax.set_xlabel("Hours from scheduled tipoff")
    ax.set_ylabel("Hourly net sales")
    ax.set_xticks(range(-3, 4), ["−3", "−2", "−1", "Tipoff", "+1", "+2", "+3"])
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda value, _: money(value)))
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(ncols=3, loc="upper right", bbox_to_anchor=(1, 1.12))
    add_source(fig, "Source: challenge transaction timestamps; scheduled tipoffs noted in methodology.")
    save(fig, "sales_relative_to_tipoff.png")


def store_type_economics() -> None:
    frame = pd.read_csv(DATA / "store_type_summary.csv")
    order = ["Concessions & Retail", "Retail", "Concessions"]
    frame = frame.set_index("store_type").loc[order].reset_index()
    labels = ["Mixed-format", "Retail", "Concessions"]
    colors = [NAVY, RED, BLUE]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.6, 6.5), gridspec_kw={"wspace": 0.34})
    fig.subplots_adjust(left=0.08, right=0.96, top=0.77, bottom=0.18)
    add_title(
        fig,
        "Mixed stores drove volume; retail carried the larger ticket",
        "Store-type performance calculated at the transaction level—not the line-item level",
    )
    bars1 = ax1.bar(labels, frame["transactions"], color=colors, width=0.62)
    ax1.set_title("Transactions", loc="left", fontsize=15, color=INK, pad=12)
    ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter("{x:,.0f}"))
    ax1.grid(axis="y")
    ax1.set_axisbelow(True)
    ax1.spines[["top", "right", "left"]].set_visible(False)
    ax1.tick_params(axis="x", rotation=15, length=0)
    for bar, value in zip(bars1, frame["transactions"]):
        ax1.text(bar.get_x() + bar.get_width()/2, value + 600, f"{value:,.0f}", ha="center", fontweight="bold", color=INK)
    ax1.set_ylim(0, frame["transactions"].max() * 1.18)

    bars2 = ax2.bar(labels, frame["average_transaction_value"], color=colors, width=0.62)
    ax2.set_title("Average transaction value", loc="left", fontsize=15, color=INK, pad=12)
    ax2.yaxis.set_major_formatter(mtick.StrMethodFormatter("${x:,.0f}"))
    ax2.grid(axis="y")
    ax2.set_axisbelow(True)
    ax2.spines[["top", "right", "left"]].set_visible(False)
    ax2.tick_params(axis="x", rotation=15, length=0)
    for bar, value in zip(bars2, frame["average_transaction_value"]):
        ax2.text(bar.get_x() + bar.get_width()/2, value + 2, f"${value:.2f}", ha="center", fontweight="bold", color=INK)
    ax2.set_ylim(0, frame["average_transaction_value"].max() * 1.2)
    add_source(fig)
    save(fig, "store_type_economics.png")


def customer_frequency() -> None:
    frame = pd.read_csv(DATA / "customer_frequency_summary.csv")
    frame["label"] = frame["games_purchased"].map({1: "1 game", 2: "2 games", 3: "3 games"})
    fig, ax = plt.subplots(figsize=(11.5, 6.4))
    fig.subplots_adjust(left=0.12, right=0.95, top=0.78, bottom=0.18)
    add_title(
        fig,
        "Three-game purchasers were 1.9% of customers but 13.5% of sales",
        "Descriptive cohort comparison across the observed three-game window",
    )
    x = np.arange(len(frame))
    width = 0.34
    bars1 = ax.bar(x - width/2, frame["customer_share"] * 100, width, label="Customer share", color=BLUE)
    bars2 = ax.bar(x + width/2, frame["sales_share"] * 100, width, label="Sales share", color=RED)
    ax.set_xticks(x, frame["label"])
    ax.set_ylabel("Share of total")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_ylim(0, 100)
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="x", length=0)
    for bars in [bars1, bars2]:
        for bar in bars:
            value = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, value + 1.5, f"{value:.1f}%", ha="center", fontsize=10, fontweight="bold", color=INK)
    ax.legend(ncols=2, loc="upper right")
    add_source(fig, "Source: challenge sales data; customers identified by CustomerAccount within the three games.")
    save(fig, "customer_frequency.png")


def main() -> None:
    apply_style()
    revenue_mix()
    game_trend()
    timing_relative_to_tipoff()
    store_type_economics()
    customer_frequency()
    print(f"Rendered 5 charts to {ASSETS}")


if __name__ == "__main__":
    main()
