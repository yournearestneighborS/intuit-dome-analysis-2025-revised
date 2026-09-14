# Data directory

## `processed`

The committed CSVs are de-identified aggregates created from the private challenge workbook. They are the only data required to run the notebook and render the charts.

| File | Grain | Purpose |
|---|---|---|
| `headline_metrics.csv` | One row per metric | Reconciled headline values and definitions |
| `business_vertical_summary.csv` | Business vertical | Sales share, attributable transactions, and customer spend |
| `mixed_store_vertical_summary.csv` | Business vertical within mixed stores | Product-mix check for concessions-and-retail locations |
| `store_type_summary.csv` | Store type | Transaction-level revenue, volume, and ticket metrics |
| `game_summary.csv` | Game | Sales, transactions, customers, ticket, and schedule anchors |
| `game_hour_summary.csv` | Game × hour relative to tipoff | Tipoff-normalized timing analysis |
| `game_clock_hour_summary.csv` | Game × local clock hour | Reconciliation and diagnostic use |
| `store_performance_summary.csv` | Store | Aggregate store performance |
| `customer_frequency_summary.csv` | Games purchased | De-identified purchase-frequency cohorts |
| `store_entry_summary.csv` | Game | Entry-event, unique-ID, repeat-event, and mapping counts |
| `store_entry_hour_summary.csv` | Game × hour relative to tipoff | Aggregate entry-event timing |
| `unmatched_entry_checkpoints.csv` | Checkpoint | Missing lookup coverage |
| `arena_entry_summary.csv` | Event | Aggregate arena entry-scan quality checks |
| `sheet_inventory.csv` | Worksheet | Source workbook inventory |
| `data_quality_summary.csv` | Validation check | Pass, review, and blocker findings |

Field-level definitions are in [`docs/DATA_DICTIONARY.md`](../docs/DATA_DICTIONARY.md).

## `raw`

Local-only location for the source workbook. Its contents are ignored by Git. Do not commit the workbook unless the data owner has explicitly authorized redistribution.

