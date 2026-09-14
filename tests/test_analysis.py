from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.clippers_analysis import (
    SourceData,
    attach_store_metadata,
    build_public_tables,
    build_transaction_table,
    write_public_tables,
)


def make_source() -> SourceData:
    sales = pd.DataFrame(
        [
            [1, "C1", "P1", "Water", "Drink", "Food And Beverage", 1, 10.0, 0.0, "A", "2025-04-24 18:10"],
            [1, "C1", "P2", "Snack", "Food", "Food And Beverage", 1, 5.0, 0.0, "A", "2025-04-24 18:10"],
            [2, "C2", "P3", "Jersey", "Apparel", "Retail", 1, 100.0, 0.0, "B", "2025-04-24 19:10"],
            [3, "C1", "P4", "Meal", "Food", "Food And Beverage", 1, 20.0, 0.0, "C", "2025-04-24 20:10"],
            [3, "C1", "P5", "Cap", "Apparel", "Retail", 1, 30.0, 0.0, "C", "2025-04-24 20:10"],
            [4, "C1", "P6", "Meal", "Food", "Food And Beverage", 1, 20.0, 0.0, "A", "2025-04-26 14:15"],
        ],
        columns=[
            "TransactionId", "CustomerAccount", "ItemId", "ProductName", "Category",
            "BusinessVertical", "Quantity", "NetAmount", "DiscountAmount", "Store",
            "TransactionDateTime",
        ],
    )
    sales["TransactionDateTime"] = pd.to_datetime(sales["TransactionDateTime"])
    sales["game_date"] = pd.to_datetime(
        ["2025-04-24"] * 5 + ["2025-04-26"]
    )
    sales["source_sheet"] = "synthetic"

    stores = pd.DataFrame(
        [
            ["A", "Stand A", "Concessions", "Main", "Gate A"],
            ["B", "Shop B", "Retail", "Main", "Gate B"],
            ["C", "Mixed C", "Concessions & Retail", "Terrace", "Gate C"],
        ],
        columns=["Store Number", "Store Name", "Store Type", "Location", "Checkpoint Name"],
    )
    store_entries = pd.DataFrame(
        [
            ["E1", "2025-04-24", "2025-04-24 18:00", "ENTRY-1", "Gate A", "Face"],
            ["E2", "2025-04-24", "2025-04-24 18:30", "ENTRY-1", "Gate A", "Face"],
            ["E3", "2025-04-24", "2025-04-24 18:45", "ENTRY-2", "Unknown", "Pass"],
            ["E4", "2025-04-24", "2025-04-24 18:50", pd.NA, "Gate A", "Pass"],
        ],
        columns=["eventid", "StoreEnterDate", "StoreEnterDateTime", "NBAId", "CheckpointName", "accessmethodname"],
    )
    store_entries["StoreEnterDateTime"] = pd.to_datetime(store_entries["StoreEnterDateTime"])
    store_entries["game_date"] = pd.Timestamp("2025-04-24")
    store_entries["source_sheet"] = "synthetic"

    arena_entries = pd.DataFrame(
        [
            ["LA250424", "ARENA-1", "2025-04-25 01:00", "North", "Pass", "100"],
            ["LA250424", pd.NA, "2025-04-25 01:05", "North", "Pass", "100"],
        ],
        columns=["EventName", "RedeemingFanNBAId", "RedemptionDateTimeUTC", "DeviceLocation", "RedemptionMethod", "SectionName"],
    )
    arena_entries["RedeemingFanNBAId"] = arena_entries["RedeemingFanNBAId"].astype("string")
    arena_entries["RedemptionDateTimeUTC"] = pd.to_datetime(arena_entries["RedemptionDateTimeUTC"])

    customers = pd.DataFrame(
        [["CUSTOMER-1", "C1", 5.0, "2024-01-01"], ["CUSTOMER-2", "C2", 8.0, "2024-02-01"]],
        columns=["NBAId", "CustomerAccount", "DistanceToIntuitDome", "AppCreatedDatetime"],
    )
    sheet_inventory = pd.DataFrame(
        [{"sheet": "Arena Pricing Map", "rows": 0, "columns": 0, "exact_duplicate_rows": 0, "missing_cells": 0}]
    )
    return SourceData(sales, store_entries, arena_entries, customers, stores, sheet_inventory)


class AnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = make_source()

    def test_store_join_preserves_rows_and_sales(self) -> None:
        mapped = attach_store_metadata(self.source.sales, self.source.stores)
        self.assertEqual(len(mapped), len(self.source.sales))
        self.assertAlmostEqual(mapped["NetAmount"].sum(), 185.0)
        self.assertTrue((mapped["store_merge_status"] == "both").all())

    def test_duplicate_store_keys_fail_fast(self) -> None:
        duplicated = pd.concat([self.source.stores, self.source.stores.iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "Store Number must be unique"):
            attach_store_metadata(self.source.sales, duplicated)

    def test_transaction_value_is_not_mean_line_item(self) -> None:
        mapped = attach_store_metadata(self.source.sales, self.source.stores)
        transactions = build_transaction_table(mapped)
        concessions = transactions.loc[transactions["store_type"] == "Concessions", "net_sales"]
        self.assertEqual(len(transactions), 4)
        self.assertAlmostEqual(concessions.mean(), 17.5)
        self.assertNotAlmostEqual(concessions.mean(), self.source.sales["NetAmount"].mean())

    def test_vertical_transaction_denominator_is_explicit(self) -> None:
        tables = build_public_tables(self.source)
        vertical = tables["business_vertical_summary"].set_index("business_vertical")
        self.assertAlmostEqual(vertical.loc["Food And Beverage", "net_sales"], 55.0)
        self.assertEqual(vertical.loc["Food And Beverage", "attributable_transactions"], 3)
        self.assertAlmostEqual(vertical.loc["Food And Beverage", "average_attributable_transaction"], 55 / 3)
        self.assertAlmostEqual(vertical.loc["Retail", "average_attributable_transaction"], 65.0)

    def test_customer_frequency_uses_distinct_game_dates(self) -> None:
        summary = build_public_tables(self.source)["customer_frequency_summary"].set_index("games_purchased")
        self.assertEqual(summary.loc[1, "customers"], 1)
        self.assertEqual(summary.loc[2, "customers"], 1)
        self.assertAlmostEqual(summary.loc[2, "net_sales"], 85.0)

    def test_entry_rows_are_events_and_repeats_are_counted(self) -> None:
        summary = build_public_tables(self.source)["store_entry_summary"].iloc[0]
        self.assertEqual(summary["entry_events"], 4)
        self.assertEqual(summary["unique_entry_ids"], 2)
        self.assertEqual(summary["repeat_entry_events"], 1)
        self.assertEqual(summary["missing_entry_ids"], 1)
        self.assertEqual(summary["mapped_entry_events"], 3)

    def test_identifier_mismatch_blocks_conversion_claim(self) -> None:
        quality = build_public_tables(self.source)["data_quality_summary"]
        linkage = quality.loc[quality["area"] == "Linkage"].set_index("metric")
        self.assertEqual(linkage.loc["Store-entry IDs present in CustomerIDs", "value"], 0)
        self.assertEqual(linkage.loc["Store-entry IDs present in CustomerIDs", "status"], "Blocker")

    def test_public_outputs_exclude_direct_identifiers(self) -> None:
        tables = build_public_tables(self.source)
        with tempfile.TemporaryDirectory() as directory:
            paths = write_public_tables(tables, directory)
            combined = "\n".join(Path(path).read_text(encoding="utf-8") for path in paths)
        for sensitive_value in ["C1", "C2", "ENTRY-1", "CUSTOMER-1", "ARENA-1"]:
            self.assertNotIn(sensitive_value, combined)
        forbidden_columns = {"TransactionId", "CustomerAccount", "NBAId", "eventid", "ItemId"}
        for table in tables.values():
            self.assertTrue(forbidden_columns.isdisjoint(table.columns))


if __name__ == "__main__":
    unittest.main()
