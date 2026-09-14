# Audit issues and implemented fixes

| Original issue | Risk | Implemented fix |
|---|---|---|
| Mean line-item value labeled as average transaction | Understates or distorts ticket economics | Aggregate to one row per game/transaction before calculating mean and median |
| “Food & beverage is 1.7% better” | Incorrect arithmetic and ambiguous wording | Report 1.69× or 69.1% higher, with both numerator and denominator disclosed |
| Absolute 6–8 PM labeled as universal peak | Apr 26 started four hours earlier | Normalize all timestamps to scheduled tipoff; final pregame hour is the supported finding |
| Manually labeled pregame, halftime, and quarter chart | Phases were not generated from data | Replace with reproducible relative-hour chart; do not infer quarter boundaries |
| Store-entry and purchase data described as linked | No shared person IDs | Remove conversion claim; document zero identifier overlap as a blocker |
| StoreEntries row count treated like foot traffic/attendance | Repeat events inflate people count | Label rows as events and report unique IDs plus repeat-event counts separately |
| Store merge not protected against key duplication | A bad lookup could multiply rows and sales | Require unique keys, use a validated many-to-one merge, and reconcile rows and dollars |
| CustomerIDs loaded but not used | Implied linkage without evidence | Use it only for coverage/compatibility diagnostics; document why account conversion is unavailable |
| Duplicate-looking sales rows silently ignored | Totals may be biased either way | Flag 94 rows and retain them because no line-level primary key or deduplication rule exists |
| Zero-net lines omitted from interpretation | Transaction counts and ticket distributions need context | Report 1,169 zero-net lines and 578 zero-net transactions |
| Empty Arena Pricing Map sheet not disclosed | Creates a false expectation of pricing analysis | Record the zero-row sheet in inventory and limitations |
| Notebook depended on current working directory | Breaks reproducibility from the repository root | Find the project root dynamically and use repository-relative paths |
| No dependencies or tests | Results could not be validated automatically | Add pinned requirements and eight synthetic unit tests |
| Report referenced missing figures | Written claims were not visually supported | Include generated figures, captions, metric definitions, and limitations in a rebuilt report |
| Slide deck contained unsupported claims | Executive output overstated evidence | Rebuild around four defensible findings, explicit measurement gaps, and testable recommendations |
| Raw workbook committed publicly | Potential redistribution and privacy risk | Exclude raw data, add `DATA_USE.md`, and publish only aggregates without direct identifiers |

