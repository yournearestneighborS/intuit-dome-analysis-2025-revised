# Methodology

## Scope

The analysis covers three Clippers home playoff games against Denver on April 24, April 26, and May 1, 2025. It uses sales lines, store-entry events, arena entry scans, a customer lookup, and a store lookup from the supplied workbook.

The primary analytical unit is a **transaction**. Store-entry tables are used only for event-count and mapping diagnostics because their person identifiers cannot be linked to purchases.

## Source inventory

| Source | Rows | Role |
|---|---:|---|
| Sales sheets | 60,369 | Net sales, products, verticals, stores, customer accounts, timestamps |
| StoreEntries sheets | 49,223 | Store-entry events and checkpoint labels |
| EntryScans | 42,499 | Arena entry-scan events |
| CustomerIDs | 38,676 | Account/ID crosswalk; contains 16,747 exact duplicate rows |
| StoreNames | 38 | Unique store and checkpoint mapping |
| Arena Pricing Map | 0 | Empty; not analytically usable |

## Cleaning rules

- Column names are trimmed.
- Store, customer, and ID fields are converted to nullable strings and stripped of leading/trailing whitespace.
- The known mojibake sequence `Ã‰` is repaired to `É` for readable checkpoint output.
- Transaction and entry timestamps are parsed with invalid values coerced to missing so the validation layer can count them.
- `NetAmount` is parsed as numeric.
- No duplicate-looking sales row is removed automatically.

## Store mapping

`StoreNames.Store Number` is required to be unique. Sales are joined with `validate="many_to_one"`. The pipeline asserts that:

1. row count does not change;
2. net sales do not change within half a cent; and
3. every sales row receives store metadata.

All 60,369 sales lines map successfully.

Store entries are mapped separately on checkpoint name. Coverage is 44,135 of 49,223 events, or 89.7%. The two unmapped labels are `D'USSÉ Cognac Club` (2,617) and `Club Grey Goose` (2,471); neither appears in `StoreNames`.

## Transaction construction

A transaction is a unique `(game_date, TransactionId)` pair. The pipeline verifies that each transaction has only one customer account and one store, then aggregates all of its line items.

Average transaction value is:

\[
\text{ATV}=\frac{\sum \text{NetAmount}}{\text{unique transactions}}
\]

It is not the mean of line-item `NetAmount`. This distinction changes the store-type values materially.

## Business verticals

Net sales are additive across verticals. A vertical's attributable transaction count is the number of transactions containing at least one line from that vertical. The 609 transactions that contain more than one vertical appear in each relevant denominator; therefore vertical transaction counts should not be summed to obtain the overall transaction count.

“Food & beverage is 69.1% higher than retail” is calculated as:

\[
\frac{725{,}426.00}{428{,}929.50}-1=69.1\%
\]

The equivalent ratio is 1.69×.

## Time normalization

The games did not share a clock-time start. Scheduled tipoff anchors are:

| Game | Scheduled tipoff used |
|---|---|
| Game 3, Apr 24 | 7:00 PM local |
| Game 4, Apr 26 | 3:00 PM local |
| Game 6, May 1 | 7:00 PM local |

Each transaction is assigned:

\[
\text{relative hour}=\left\lfloor\frac{\text{transaction time}-\text{tipoff}}{60\text{ minutes}}\right\rfloor
\]

Thus hour −1 is the final 60 minutes before scheduled tipoff, hour 0 is the first hour beginning at tipoff, and hour +1 is the following hour. The analysis does not infer halftime or quarter boundaries from transaction timestamps.

Official game durations are cited only as event context: [Apr 24, 2:19](https://statsdmz.nba.com/pdfs/20250424/20250424_DENLAC.pdf), [Apr 26, 2:30](https://statsdmz.nba.com/pdfs/20250426/20250426_DENLAC.pdf), and [May 1, 2:13](https://statsdmz.nba.com/pdfs/20250501/20250501_DENLAC.pdf).

## Customer frequency

Purchasing accounts are grouped by the number of distinct game dates on which they purchased. No raw account is exported. The cohorts are descriptive and do not prove loyalty, household identity, ticket ownership, or incremental value.

## Entry data and conversion

StoreEntries has 49,223 rows but only 20,603 unique `NBAId` values. There are 3,549 rows with no `NBAId`. Among identified rows, 22,468 are repeat events beyond the first event per person/game. Counting all rows as attendees would therefore overstate the population.

After deduplicating the CustomerIDs crosswalk to unique ID/account pairs:

- zero StoreEntries `NBAId` values appear in CustomerIDs; and
- zero EntryScans `RedeemingFanNBAId` values appear in CustomerIDs.

Individual visitor-to-purchaser conversion, post-entry attribution, and movement paths are therefore not identifiable. Any analysis that divides purchases by raw entry-event counts would combine incompatible units and is intentionally omitted.

## Duplicate and zero-value policy

- **94 exact duplicate-looking sales lines:** retained because no immutable line ID is available. They may be duplicates or legitimate repeated items.
- **1,169 zero-net lines:** retained and disclosed.
- **578 zero-net transactions:** included in transaction counts and ticket distributions.
- **No negative-net lines:** observed.

Sensitivity analysis is recommended if a data owner supplies a line-level primary key or business rule for complimentary and fully discounted items.

## Interpretation boundary

The findings are descriptive. The source does not include attendance, open-store minutes, inventory, stockouts, staffing, queue length, wait time, promotions, cost, margin, taxes, or experiment assignment. Recommendations are framed as tests with proposed measurements, not as causal conclusions.
