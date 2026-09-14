# Processed data dictionary

All files are comma-separated UTF-8 text. Currency fields use dollars. Shares use unit fractions: `0.628` means 62.8%.

## Common fields

| Field | Definition |
|---|---|
| `game_date` | Calendar date of the game, `YYYY-MM-DD` |
| `game_label` | Display label for the game |
| `net_sales` | Sum of source `NetAmount` |
| `transactions` | Count of unique game/transaction pairs at the table's grain |
| `customers` | Count of unique purchasing accounts at the table's grain |
| `average_transaction_value` | Net sales divided by transaction count |
| `median_transaction_value` | Median transaction-level net sales |
| `sales_share` | Share of total sales within the table's population |

## `headline_metrics.csv`

| Field | Definition |
|---|---|
| `metric` | Stable machine-readable metric name |
| `value` | Numeric metric value |
| `definition` | Human-readable denominator and scope |

## `business_vertical_summary.csv`

| Field | Definition |
|---|---|
| `business_vertical` | Food And Beverage, Retail, or Service Items |
| `line_items` | Source line rows assigned to the vertical |
| `customer_count` | Purchasing accounts with at least one line in the vertical |
| `attributable_transactions` | Transactions containing at least one line in the vertical |
| `average_attributable_transaction` | Vertical sales divided by attributable transactions |
| `median_attributable_transaction` | Median vertical amount within attributable transactions |
| `average_customer_spend` | Mean three-game vertical spend per customer |
| `median_customer_spend` | Median three-game vertical spend per customer |

## `mixed_store_vertical_summary.csv`

Same vertical definitions, limited to stores classified `Concessions & Retail`.

## `store_type_summary.csv`

One row per store type. Adds transaction-level average and median, unique customers, and share of all net sales.

## `game_summary.csv`

| Field | Definition |
|---|---|
| `zero_net_transactions` | Transactions whose summed line values equal zero |
| `scheduled_tipoff` | Local, timezone-naive schedule anchor used for relative time |
| `official_game_duration` | Duration listed in the official NBA game book, `H:MM` |

## `game_hour_summary.csv`

| Field | Definition |
|---|---|
| `relative_hour` | Floored hours between transaction time and scheduled tipoff |
| `net_sales` | Sales in the game/hour bucket |
| `transactions` | Transactions in the game/hour bucket |
| `customers` | Unique accounts purchasing in the bucket |

## `game_clock_hour_summary.csv`

| Field | Definition |
|---|---|
| `clock_hour` | Local transaction hour from 0 through 23 |

This table is included for audit and reconciliation. Relative-hour analysis is preferred across games.

## `store_performance_summary.csv`

| Field | Definition |
|---|---|
| `store_number` | Operational store code; not a person or transaction identifier |
| `store_name` | Store display name |
| `store_type` | Concessions, Retail, or Concessions & Retail |
| `location` | Arena level or plaza grouping |
| `games_active` | Distinct games with at least one transaction |

## `customer_frequency_summary.csv`

| Field | Definition |
|---|---|
| `games_purchased` | Number of the three games with a purchase |
| `customers` | Accounts in the frequency cohort |
| `average_customer_spend` | Mean three-game net sales per account in the cohort |
| `median_customer_spend` | Median three-game net sales per account in the cohort |
| `average_transactions` | Mean transaction count per account in the cohort |
| `customer_share` | Cohort share of all purchasing accounts |

## Store-entry files

`store_entry_summary.csv` is one row per game and includes:

| Field | Definition |
|---|---|
| `entry_events` | StoreEntries rows; not attendee count |
| `unique_entry_ids` | Unique pseudonymous IDs observed in the game |
| `missing_entry_ids` | Entry events without an NBAId; excluded from repeat-person calculations |
| `mapped_entry_events` | Events whose checkpoint matched StoreNames |
| `repeat_entry_events` | Identified events after the first event for the same ID/game |
| `store_mapping_rate` | Mapped events divided by all entry events |

`store_entry_hour_summary.csv` applies the same event and unique-ID counts by relative hour. `unmatched_entry_checkpoints.csv` lists unmapped checkpoint labels, event counts, and games observed.

## `arena_entry_summary.csv`

| Field | Definition |
|---|---|
| `event_name` | Source event label |
| `arena_entry_events` | EntryScans rows |
| `unique_entry_ids` | Unique nonmissing IDs |
| `missing_entry_ids` | Rows without an ID |
| `records_more_than_one_utc_day_late` | Records whose UTC date is more than one day after the event date |

## Audit files

- `sheet_inventory.csv` records worksheet dimensions, exact duplicates, and missing-cell counts.
- `data_quality_summary.csv` records an analytical area, validation metric, numeric value, status (`Pass`, `Info`, `Review`, or `Blocker`), and interpretation note.
