"""Validated transformations for the Intuit Dome arena-store case study.

The public repository contains only aggregate outputs. This module is the
reproducible bridge from the privately held challenge workbook to those
outputs. No customer, account, event, transaction, or product identifier is
written by :func:`write_public_tables`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd


SALES_SHEETS: Mapping[str, str] = {
    "Retail+F&B 4.24": "2025-04-24",
    "Retail+F&B 4.26": "2025-04-26",
    "Retail+F&B 5.1": "2025-05-01",
}

STORE_ENTRY_SHEETS: Mapping[str, str] = {
    "StoreEntries 4.24": "2025-04-24",
    "StoreEntries 4.26": "2025-04-26",
    "StoreEntries 5.1": "2025-05-01",
}

GAME_CONFIG = pd.DataFrame(
    [
        {
            "game_date": "2025-04-24",
            "game_label": "Game 3 · Apr 24",
            "scheduled_tipoff": "2025-04-24 19:00:00",
            "official_game_duration": "2:19",
        },
        {
            "game_date": "2025-04-26",
            "game_label": "Game 4 · Apr 26",
            "scheduled_tipoff": "2025-04-26 15:00:00",
            "official_game_duration": "2:30",
        },
        {
            "game_date": "2025-05-01",
            "game_label": "Game 6 · May 1",
            "scheduled_tipoff": "2025-05-01 19:00:00",
            "official_game_duration": "2:13",
        },
    ]
)
GAME_CONFIG["game_date"] = pd.to_datetime(GAME_CONFIG["game_date"])
GAME_CONFIG["scheduled_tipoff"] = pd.to_datetime(GAME_CONFIG["scheduled_tipoff"])


SALES_COLUMNS = {
    "TransactionId",
    "CustomerAccount",
    "ItemId",
    "ProductName",
    "Category",
    "BusinessVertical",
    "Quantity",
    "NetAmount",
    "DiscountAmount",
    "Store",
    "TransactionDateTime",
}
STORE_ENTRY_COLUMNS = {
    "eventid",
    "StoreEnterDate",
    "StoreEnterDateTime",
    "NBAId",
    "CheckpointName",
    "accessmethodname",
}
STORE_COLUMNS = {
    "Store Number",
    "Store Name",
    "Store Type",
    "Location",
    "Checkpoint Name",
}
CUSTOMER_COLUMNS = {"NBAId", "CustomerAccount", "DistanceToIntuitDome", "AppCreatedDatetime"}
ARENA_ENTRY_COLUMNS = {
    "EventName",
    "RedeemingFanNBAId",
    "RedemptionDateTimeUTC",
    "DeviceLocation",
    "RedemptionMethod",
    "SectionName",
}


@dataclass(frozen=True)
class SourceData:
    """Cleaned, private source tables loaded from the challenge workbook."""

    sales: pd.DataFrame
    store_entries: pd.DataFrame
    arena_entries: pd.DataFrame
    customers: pd.DataFrame
    stores: pd.DataFrame
    sheet_inventory: pd.DataFrame


def _require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {missing}")


def _clean_identifier(series: pd.Series) -> pd.Series:
    """Return trimmed nullable strings without converting missing values to text."""

    return series.astype("string").str.strip()


def _normalize_checkpoint(series: pd.Series) -> pd.Series:
    """Trim checkpoint labels and repair the known UTF-8 mojibake sequence."""

    return _clean_identifier(series).str.replace("Ã‰", "É", regex=False)


def load_source_workbook(workbook: str | Path) -> SourceData:
    """Load, type, and validate all analytically relevant workbook sheets."""

    workbook = Path(workbook)
    if not workbook.is_file():
        raise FileNotFoundError(f"Workbook not found: {workbook}")

    excel = pd.ExcelFile(workbook)
    required_sheets = (
        set(SALES_SHEETS)
        | set(STORE_ENTRY_SHEETS)
        | {"EntryScans", "CustomerIDs", "StoreNames", "Arena Pricing Map"}
    )
    missing_sheets = sorted(required_sheets.difference(excel.sheet_names))
    if missing_sheets:
        raise ValueError(f"Workbook is missing required sheets: {missing_sheets}")

    inventory_rows: list[dict[str, object]] = []
    raw: dict[str, pd.DataFrame] = {}
    for sheet in excel.sheet_names:
        frame = pd.read_excel(excel, sheet_name=sheet)
        frame.columns = frame.columns.astype(str).str.strip()
        raw[sheet] = frame
        inventory_rows.append(
            {
                "sheet": sheet,
                "rows": len(frame),
                "columns": len(frame.columns),
                "exact_duplicate_rows": int(frame.duplicated().sum()),
                "missing_cells": int(frame.isna().sum().sum()),
            }
        )

    sales_parts: list[pd.DataFrame] = []
    for sheet, game_date in SALES_SHEETS.items():
        frame = raw[sheet].copy()
        _require_columns(frame, SALES_COLUMNS, sheet)
        frame["source_sheet"] = sheet
        frame["game_date"] = pd.Timestamp(game_date)
        frame["TransactionDateTime"] = pd.to_datetime(
            frame["TransactionDateTime"], errors="coerce"
        )
        for column in ["Store", "CustomerAccount", "BusinessVertical"]:
            frame[column] = _clean_identifier(frame[column])
        frame["NetAmount"] = pd.to_numeric(frame["NetAmount"], errors="coerce")
        sales_parts.append(frame)
    sales = pd.concat(sales_parts, ignore_index=True)

    entry_parts: list[pd.DataFrame] = []
    for sheet, game_date in STORE_ENTRY_SHEETS.items():
        frame = raw[sheet].copy()
        _require_columns(frame, STORE_ENTRY_COLUMNS, sheet)
        frame["source_sheet"] = sheet
        frame["game_date"] = pd.Timestamp(game_date)
        frame["StoreEnterDateTime"] = pd.to_datetime(
            frame["StoreEnterDateTime"], errors="coerce"
        )
        frame["CheckpointName"] = _normalize_checkpoint(frame["CheckpointName"])
        frame["NBAId"] = _clean_identifier(frame["NBAId"])
        entry_parts.append(frame)
    store_entries = pd.concat(entry_parts, ignore_index=True)

    arena_entries = raw["EntryScans"].copy()
    _require_columns(arena_entries, ARENA_ENTRY_COLUMNS, "EntryScans")
    arena_entries["RedeemingFanNBAId"] = _clean_identifier(
        arena_entries["RedeemingFanNBAId"]
    )
    arena_entries["RedemptionDateTimeUTC"] = pd.to_datetime(
        arena_entries["RedemptionDateTimeUTC"], errors="coerce"
    )

    customers = raw["CustomerIDs"].copy()
    _require_columns(customers, CUSTOMER_COLUMNS, "CustomerIDs")
    customers["NBAId"] = _clean_identifier(customers["NBAId"])
    customers["CustomerAccount"] = _clean_identifier(customers["CustomerAccount"])

    stores = raw["StoreNames"].copy()
    _require_columns(stores, STORE_COLUMNS, "StoreNames")
    stores["Store Number"] = _clean_identifier(stores["Store Number"])
    stores["Checkpoint Name"] = _normalize_checkpoint(stores["Checkpoint Name"])
    stores["Store Name"] = stores["Store Name"].astype("string").str.strip()
    stores["Store Type"] = stores["Store Type"].astype("string").str.strip()
    stores["Location"] = stores["Location"].astype("string").str.strip()

    return SourceData(
        sales=sales,
        store_entries=store_entries,
        arena_entries=arena_entries,
        customers=customers,
        stores=stores,
        sheet_inventory=pd.DataFrame(inventory_rows),
    )


def attach_store_metadata(
    sales: pd.DataFrame, stores: pd.DataFrame
) -> pd.DataFrame:
    """Attach store attributes with a validated many-to-one join."""

    if stores["Store Number"].duplicated().any():
        duplicate_keys = stores.loc[
            stores["Store Number"].duplicated(keep=False), "Store Number"
        ].dropna().unique()
        raise ValueError(f"Store Number must be unique; duplicates: {duplicate_keys.tolist()}")

    before_rows = len(sales)
    before_sales = float(sales["NetAmount"].sum())
    mapped = sales.merge(
        stores[["Store Number", "Store Name", "Store Type", "Location", "Checkpoint Name"]],
        left_on="Store",
        right_on="Store Number",
        how="left",
        validate="many_to_one",
        indicator="store_merge_status",
    )
    if len(mapped) != before_rows:
        raise AssertionError("Store join changed the number of sales rows")
    if not np.isclose(float(mapped["NetAmount"].sum()), before_sales, atol=0.005):
        raise AssertionError("Store join changed total net sales")
    return mapped


def build_transaction_table(mapped_sales: pd.DataFrame) -> pd.DataFrame:
    """Collapse line items to one row per game/transaction.

    `average_transaction_value` must be calculated from this table, not from
    the mean line-item amount.
    """

    keys = ["game_date", "TransactionId"]
    cardinality = mapped_sales.groupby(keys).agg(
        customer_count=("CustomerAccount", "nunique"),
        store_count=("Store", "nunique"),
    )
    invalid = cardinality.query("customer_count > 1 or store_count > 1")
    if not invalid.empty:
        raise ValueError("A transaction maps to more than one customer or store")

    transactions = (
        mapped_sales.groupby(keys, as_index=False, dropna=False)
        .agg(
            customer_account=("CustomerAccount", "first"),
            store_number=("Store", "first"),
            store_name=("Store Name", "first"),
            store_type=("Store Type", "first"),
            location=("Location", "first"),
            transaction_time=("TransactionDateTime", "min"),
            net_sales=("NetAmount", "sum"),
            line_items=("NetAmount", "size"),
            zero_net_lines=("NetAmount", lambda values: int((values == 0).sum())),
        )
        .sort_values(["game_date", "transaction_time", "TransactionId"])
        .reset_index(drop=True)
    )

    vertical_amounts = (
        mapped_sales.pivot_table(
            index=keys,
            columns="BusinessVertical",
            values="NetAmount",
            aggfunc="sum",
            fill_value=0,
        )
        .rename_axis(columns=None)
        .reset_index()
        .rename(
            columns={
                "Food And Beverage": "food_and_beverage_sales",
                "Retail": "retail_sales",
                "Service Items": "service_sales",
            }
        )
    )
    for column in ["food_and_beverage_sales", "retail_sales", "service_sales"]:
        if column not in vertical_amounts:
            vertical_amounts[column] = 0.0
    transactions = transactions.merge(vertical_amounts, on=keys, validate="one_to_one")

    config = GAME_CONFIG[["game_date", "game_label", "scheduled_tipoff"]]
    transactions = transactions.merge(config, on="game_date", validate="many_to_one")
    transactions["minutes_from_tipoff"] = (
        (transactions["transaction_time"] - transactions["scheduled_tipoff"])
        .dt.total_seconds()
        .div(60)
    )
    transactions["relative_hour"] = np.floor(
        transactions["minutes_from_tipoff"] / 60
    ).astype(int)
    transactions["clock_hour"] = transactions["transaction_time"].dt.hour
    return transactions


def _business_vertical_summary(mapped_sales: pd.DataFrame) -> pd.DataFrame:
    tx_vertical = (
        mapped_sales.groupby(
            ["game_date", "TransactionId", "BusinessVertical"], as_index=False
        )
        .agg(vertical_transaction_sales=("NetAmount", "sum"))
    )
    customer_vertical = (
        mapped_sales.groupby(["CustomerAccount", "BusinessVertical"], as_index=False)
        .agg(customer_vertical_sales=("NetAmount", "sum"))
    )
    line_summary = (
        mapped_sales.groupby("BusinessVertical", as_index=False)
        .agg(
            net_sales=("NetAmount", "sum"),
            line_items=("NetAmount", "size"),
            customer_count=("CustomerAccount", "nunique"),
        )
    )
    tx_summary = (
        tx_vertical.groupby("BusinessVertical", as_index=False)
        .agg(
            attributable_transactions=("TransactionId", "size"),
            average_attributable_transaction=("vertical_transaction_sales", "mean"),
            median_attributable_transaction=("vertical_transaction_sales", "median"),
        )
    )
    customer_summary = (
        customer_vertical.groupby("BusinessVertical", as_index=False)
        .agg(
            average_customer_spend=("customer_vertical_sales", "mean"),
            median_customer_spend=("customer_vertical_sales", "median"),
        )
    )
    result = line_summary.merge(tx_summary, on="BusinessVertical").merge(
        customer_summary, on="BusinessVertical"
    )
    result["sales_share"] = result["net_sales"] / result["net_sales"].sum()
    return result.rename(columns={"BusinessVertical": "business_vertical"}).sort_values(
        "net_sales", ascending=False
    )


def _mixed_store_vertical_summary(mapped_sales: pd.DataFrame) -> pd.DataFrame:
    mixed = mapped_sales.loc[mapped_sales["Store Type"] == "Concessions & Retail"]
    result = (
        mixed.groupby("BusinessVertical", as_index=False)
        .agg(net_sales=("NetAmount", "sum"), transactions=("TransactionId", "nunique"))
        .rename(columns={"BusinessVertical": "business_vertical"})
    )
    result["sales_share"] = result["net_sales"] / result["net_sales"].sum()
    return result.sort_values("net_sales", ascending=False)


def _store_type_summary(transactions: pd.DataFrame) -> pd.DataFrame:
    result = (
        transactions.groupby("store_type", as_index=False, dropna=False)
        .agg(
            net_sales=("net_sales", "sum"),
            transactions=("TransactionId", "size"),
            average_transaction_value=("net_sales", "mean"),
            median_transaction_value=("net_sales", "median"),
            customers=("customer_account", "nunique"),
        )
    )
    result["sales_share"] = result["net_sales"] / result["net_sales"].sum()
    return result.sort_values("net_sales", ascending=False)


def _game_summary(transactions: pd.DataFrame) -> pd.DataFrame:
    result = (
        transactions.groupby(["game_date", "game_label"], as_index=False)
        .agg(
            net_sales=("net_sales", "sum"),
            transactions=("TransactionId", "size"),
            customers=("customer_account", "nunique"),
            average_transaction_value=("net_sales", "mean"),
            median_transaction_value=("net_sales", "median"),
            zero_net_transactions=("net_sales", lambda values: int((values == 0).sum())),
        )
    )
    return result.merge(
        GAME_CONFIG, on=["game_date", "game_label"], validate="one_to_one"
    ).sort_values("game_date")


def _game_hour_summary(transactions: pd.DataFrame) -> pd.DataFrame:
    result = (
        transactions.groupby(
            ["game_date", "game_label", "relative_hour"], as_index=False
        )
        .agg(
            net_sales=("net_sales", "sum"),
            transactions=("TransactionId", "size"),
            customers=("customer_account", "nunique"),
        )
    )
    result["average_transaction_value"] = result["net_sales"] / result["transactions"]
    return result.sort_values(["game_date", "relative_hour"])


def _game_clock_hour_summary(transactions: pd.DataFrame) -> pd.DataFrame:
    result = (
        transactions.groupby(
            ["game_date", "game_label", "clock_hour"], as_index=False
        )
        .agg(net_sales=("net_sales", "sum"), transactions=("TransactionId", "size"))
    )
    result["average_transaction_value"] = result["net_sales"] / result["transactions"]
    return result.sort_values(["game_date", "clock_hour"])


def _store_performance_summary(transactions: pd.DataFrame) -> pd.DataFrame:
    result = (
        transactions.groupby(
            ["store_number", "store_name", "store_type", "location"],
            as_index=False,
            dropna=False,
        )
        .agg(
            net_sales=("net_sales", "sum"),
            transactions=("TransactionId", "size"),
            customers=("customer_account", "nunique"),
            games_active=("game_date", "nunique"),
            average_transaction_value=("net_sales", "mean"),
        )
    )
    return result.sort_values("net_sales", ascending=False)


def _customer_frequency_summary(transactions: pd.DataFrame) -> pd.DataFrame:
    customer = (
        transactions.groupby("customer_account", as_index=False)
        .agg(
            games_purchased=("game_date", "nunique"),
            net_sales=("net_sales", "sum"),
            transactions=("TransactionId", "size"),
        )
    )
    result = (
        customer.groupby("games_purchased", as_index=False)
        .agg(
            customers=("customer_account", "size"),
            net_sales=("net_sales", "sum"),
            average_customer_spend=("net_sales", "mean"),
            median_customer_spend=("net_sales", "median"),
            average_transactions=("transactions", "mean"),
        )
    )
    result["customer_share"] = result["customers"] / result["customers"].sum()
    result["sales_share"] = result["net_sales"] / result["net_sales"].sum()
    return result.sort_values("games_purchased")


def _store_entry_tables(
    store_entries: pd.DataFrame, stores: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if stores["Checkpoint Name"].duplicated().any():
        raise ValueError("Checkpoint Name must be unique for the entry mapping")
    mapped = store_entries.merge(
        stores[["Checkpoint Name", "Store Number", "Store Name", "Store Type"]],
        left_on="CheckpointName",
        right_on="Checkpoint Name",
        how="left",
        validate="many_to_one",
        indicator="entry_merge_status",
    )
    mapped = mapped.merge(
        GAME_CONFIG[["game_date", "game_label", "scheduled_tipoff"]],
        on="game_date",
        validate="many_to_one",
    )
    mapped["minutes_from_tipoff"] = (
        (mapped["StoreEnterDateTime"] - mapped["scheduled_tipoff"])
        .dt.total_seconds()
        .div(60)
    )
    mapped["relative_hour"] = np.floor(mapped["minutes_from_tipoff"] / 60).astype(int)

    by_game = (
        mapped.groupby(["game_date", "game_label"], as_index=False)
        .agg(
            entry_events=("eventid", "size"),
            unique_entry_ids=("NBAId", "nunique"),
            missing_entry_ids=("NBAId", lambda values: int(values.isna().sum())),
            mapped_entry_events=(
                "entry_merge_status",
                lambda values: int((values == "both").sum()),
            ),
        )
    )
    identified = mapped.loc[mapped["NBAId"].notna()].sort_values("StoreEnterDateTime").copy()
    identified["is_repeat_entry"] = identified.duplicated(
        ["game_date", "NBAId"], keep="first"
    )
    repeats = (
        identified.groupby("game_date", as_index=False)
        .agg(repeat_entry_events=("is_repeat_entry", "sum"))
    )
    by_game = by_game.merge(repeats, on="game_date", validate="one_to_one")
    by_game["store_mapping_rate"] = by_game["mapped_entry_events"] / by_game["entry_events"]

    by_hour = (
        mapped.groupby(["game_date", "game_label", "relative_hour"], as_index=False)
        .agg(entry_events=("eventid", "size"), unique_entry_ids=("NBAId", "nunique"))
        .sort_values(["game_date", "relative_hour"])
    )

    unmatched = (
        mapped.loc[mapped["entry_merge_status"] != "both"]
        .groupby("CheckpointName", as_index=False)
        .agg(entry_events=("eventid", "size"), games_observed=("game_date", "nunique"))
        .rename(columns={"CheckpointName": "checkpoint_name"})
        .sort_values("entry_events", ascending=False)
    )
    return by_game, by_hour, unmatched


def _arena_entry_summary(arena_entries: pd.DataFrame) -> pd.DataFrame:
    game_dates = {
        "LA250424": pd.Timestamp("2025-04-24"),
        "LA250426": pd.Timestamp("2025-04-26"),
        "LA250501": pd.Timestamp("2025-05-01"),
    }
    working = arena_entries.copy()
    working["game_date"] = working["EventName"].map(game_dates)
    utc_calendar_date = working["RedemptionDateTimeUTC"].dt.normalize()
    working["days_after_game_date"] = (utc_calendar_date - working["game_date"]).dt.days
    result = (
        working.groupby(["EventName", "game_date"], as_index=False)
        .agg(
            arena_entry_events=("RedeemingFanNBAId", "size"),
            unique_entry_ids=("RedeemingFanNBAId", "nunique"),
            missing_entry_ids=("RedeemingFanNBAId", lambda values: int(values.isna().sum())),
            records_more_than_one_utc_day_late=(
                "days_after_game_date",
                lambda values: int((values > 1).sum()),
            ),
        )
        .rename(columns={"EventName": "event_name"})
    )
    return result.sort_values("game_date")


def _headline_metrics(
    mapped_sales: pd.DataFrame,
    transactions: pd.DataFrame,
    store_entries: pd.DataFrame,
) -> pd.DataFrame:
    revenue = float(mapped_sales["NetAmount"].sum())
    vertical = mapped_sales.groupby("BusinessVertical")["NetAmount"].sum()
    fnb = float(vertical.get("Food And Beverage", 0.0))
    retail = float(vertical.get("Retail", 0.0))
    service = float(vertical.get("Service Items", 0.0))
    values = [
        ("net_sales", revenue, "Sum of line-item NetAmount across all three games"),
        ("transactions", float(len(transactions)), "Unique game/transaction pairs"),
        (
            "customers",
            float(transactions["customer_account"].nunique()),
            "Unique purchasing CustomerAccount values",
        ),
        ("food_and_beverage_sales", fnb, "Net sales attributed to Food And Beverage"),
        ("retail_sales", retail, "Net sales attributed to Retail"),
        ("service_sales", service, "Net sales attributed to Service Items"),
        ("food_and_beverage_share", fnb / revenue, "Food And Beverage share of net sales"),
        ("retail_share", retail / revenue, "Retail share of net sales"),
        ("fnb_to_retail_ratio", fnb / retail, "Food And Beverage sales divided by Retail sales"),
        (
            "fnb_percent_higher_than_retail",
            (fnb / retail) - 1,
            "Relative difference: Food And Beverage versus Retail sales",
        ),
        ("store_entry_events", float(len(store_entries)), "Store-entry event rows; not attendance"),
        (
            "unique_store_entry_ids",
            float(store_entries["NBAId"].nunique()),
            "Unique pseudonymous NBAId values in StoreEntries",
        ),
    ]
    return pd.DataFrame(values, columns=["metric", "value", "definition"])


def _data_quality_summary(
    source: SourceData,
    mapped_sales: pd.DataFrame,
    transactions: pd.DataFrame,
    store_entry_by_game: pd.DataFrame,
    unmatched_entries: pd.DataFrame,
) -> pd.DataFrame:
    sales = source.sales
    entries = source.store_entries
    customers = source.customers
    arena_entries = source.arena_entries
    customer_pairs = customers[["NBAId", "CustomerAccount"]].dropna().drop_duplicates()
    customer_nba_ids = set(customer_pairs["NBAId"])
    customer_accounts = set(customer_pairs["CustomerAccount"])
    raw_sales_columns = sorted(SALES_COLUMNS)
    sales_duplicates = int(sales[raw_sales_columns].duplicated().sum())
    rows: list[dict[str, object]] = []

    def add(area: str, metric: str, value: object, status: str, note: str) -> None:
        rows.append(
            {"area": area, "metric": metric, "value": value, "status": status, "note": note}
        )

    add("Sales", "Line-item rows", len(sales), "Info", "Three sales worksheets combined")
    add("Sales", "Unique transactions", len(transactions), "Pass", "Game date + TransactionId")
    add("Sales", "Exact duplicate-looking line rows", sales_duplicates, "Review", "No line ID is available, so these are flagged and retained")
    add("Sales", "Zero-net line rows", int((sales["NetAmount"] == 0).sum()), "Review", "Retained; may reflect complimentary or fully discounted items")
    add("Sales", "Negative-net line rows", int((sales["NetAmount"] < 0).sum()), "Pass", "None observed")
    add("Sales", "Missing transaction timestamps", int(sales["TransactionDateTime"].isna().sum()), "Pass", "Datetime coercion check")
    add("Mapping", "Sales rows mapped to a store", int((mapped_sales["store_merge_status"] == "both").sum()), "Pass", "100% of sales rows")
    add("Mapping", "Store-entry mapping rate", float(store_entry_by_game["mapped_entry_events"].sum() / store_entry_by_game["entry_events"].sum()), "Review", "Two checkpoint labels have no StoreNames row")
    add("Mapping", "Unmapped store-entry events", int(unmatched_entries["entry_events"].sum()), "Review", "D'USSÉ Cognac Club and Club Grey Goose")
    add("Store entries", "Event rows", len(entries), "Info", "Rows are entry events, not attendees")
    add("Store entries", "Unique entry IDs", int(entries["NBAId"].nunique()), "Info", "A person can generate multiple entry events")
    add("Store entries", "Missing entry IDs", int(entries["NBAId"].isna().sum()), "Review", "Missing IDs are excluded from repeat-person calculations")
    add("Store entries", "Repeat identified events beyond first per person/game", int(store_entry_by_game["repeat_entry_events"].sum()), "Review", "Calculated only where NBAId is present; rows are not attendance")
    add("Customer map", "Rows", len(customers), "Info", "CustomerIDs worksheet")
    add("Customer map", "Exact duplicate rows", int(customers.duplicated().sum()), "Review", "Deduplicate before any account-level use")
    add("Customer map", "Sales rows with mapped CustomerAccount", int(sales["CustomerAccount"].isin(customer_accounts).sum()), "Review", "Coverage is incomplete")
    add("Linkage", "Store-entry IDs present in CustomerIDs", int(entries["NBAId"].isin(customer_nba_ids).sum()), "Blocker", "Zero overlap; store-entry-to-purchase conversion is not identifiable")
    add("Linkage", "Arena-entry IDs present in CustomerIDs", int(arena_entries["RedeemingFanNBAId"].isin(customer_nba_ids).sum()), "Blocker", "Zero overlap; arena-entry-to-purchase conversion is not identifiable")
    add("Arena entries", "Missing entry IDs", int(arena_entries["RedeemingFanNBAId"].isna().sum()), "Review", "Event counts include these rows; unique-ID counts do not")
    add("Workbook", "Arena Pricing Map rows", int(source.sheet_inventory.loc[source.sheet_inventory["sheet"] == "Arena Pricing Map", "rows"].iloc[0]), "Review", "Worksheet is empty")
    return pd.DataFrame(rows)


def build_public_tables(source: SourceData) -> dict[str, pd.DataFrame]:
    """Create aggregate, de-identified tables used by the public analysis."""

    mapped_sales = attach_store_metadata(source.sales, source.stores)
    if (mapped_sales["store_merge_status"] != "both").any():
        raise ValueError("All sales rows must map to StoreNames before aggregation")
    transactions = build_transaction_table(mapped_sales)
    store_entry_by_game, store_entry_by_hour, unmatched_entries = _store_entry_tables(
        source.store_entries, source.stores
    )

    tables = {
        "headline_metrics": _headline_metrics(mapped_sales, transactions, source.store_entries),
        "business_vertical_summary": _business_vertical_summary(mapped_sales),
        "mixed_store_vertical_summary": _mixed_store_vertical_summary(mapped_sales),
        "store_type_summary": _store_type_summary(transactions),
        "game_summary": _game_summary(transactions),
        "game_hour_summary": _game_hour_summary(transactions),
        "game_clock_hour_summary": _game_clock_hour_summary(transactions),
        "store_performance_summary": _store_performance_summary(transactions),
        "customer_frequency_summary": _customer_frequency_summary(transactions),
        "store_entry_summary": store_entry_by_game,
        "store_entry_hour_summary": store_entry_by_hour,
        "unmatched_entry_checkpoints": unmatched_entries,
        "arena_entry_summary": _arena_entry_summary(source.arena_entries),
        "sheet_inventory": source.sheet_inventory,
    }
    tables["data_quality_summary"] = _data_quality_summary(
        source,
        mapped_sales,
        transactions,
        store_entry_by_game,
        unmatched_entries,
    )
    return tables


def write_public_tables(
    tables: Mapping[str, pd.DataFrame], output_dir: str | Path
) -> list[Path]:
    """Write deterministic aggregate CSVs and return their paths."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, frame in tables.items():
        public = frame.copy()
        for column in public.select_dtypes(include=["datetime", "datetimetz"]).columns:
            date_format = "%Y-%m-%d" if column.endswith("_date") else "%Y-%m-%d %H:%M:%S"
            public[column] = public[column].dt.strftime(date_format)
        float_columns = public.select_dtypes(include=["floating"]).columns
        public[float_columns] = public[float_columns].round(6)
        path = output_dir / f"{name}.csv"
        public.to_csv(path, index=False, lineterminator="\n")
        written.append(path)
    return written


def build_and_write_public_data(
    workbook: str | Path, output_dir: str | Path
) -> dict[str, pd.DataFrame]:
    """Convenience entry point used by the command-line build script."""

    source = load_source_workbook(workbook)
    tables = build_public_tables(source)
    write_public_tables(tables, output_dir)
    return tables
