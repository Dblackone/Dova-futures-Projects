# The bid comparison workbook

Six sheets. Build them in this order — each depends on the one before.

The workbook is the evidence base for everything else you produce. Its job is to
let a sceptical reader retrace every figure back to a source document without
asking you a single question.

## Colour convention

Apply this consistently and state it in a legend on the first sheet. It lets a
reader tell at a glance what is evidence and what is inference.

| Colour | Meaning |
|---|---|
| Blue text | Figure transcribed from a bidder's document |
| Black text | Calculated by formula |
| Yellow fill | Key input, or a value you imputed — change these to re-run the comparison |
| Orange fill | Non-compliance or exception flag |

Use real formulas, not pasted values. A client who wants to test a different VAT
rate, reference date or imputed figure should be able to change one yellow cell
and watch the workbook update. Hard-coded totals make the workbook a picture of
an answer rather than a working model.

## Sheet 1 — Summary

One column per bidder. Rows:

- Source document filename
- Quote date
- Equipment or brand offered
- Subtotal excluding tax, as quoted
- Tax
- Total as quoted
- Normalisation adjustments (linked from Sheet 4)
- Adjusted total, like-for-like
- Rank among compliant bids
- Premium over the lowest compliant bid, as a percentage
- Validity status at the reference date
- One-line assessment

Close with a short "how to read this workbook" block naming each sheet and what
it does. Someone opening this cold should not have to guess.

## Sheet 2 — Bid Tab

The core tabulation. Rows are the client's BoQ lines; columns are the bidders.

Columns: BoQ item number, description as the client wrote it, quantity, unit,
then one column per bidder, then median / lowest / highest across the compliant
bids, then a notes-and-exceptions column.

The median, low and high columns should cover comparable bids only. Including a
bid that offers different equipment makes the median meaningless.

Below the BoQ block:

- A row for items priced **outside** the BoQ, per bidder, with the detail broken
  out beneath the sheet. These belong in the subtotal the bidder printed but not
  in the tendered scope.
- Subtotal, tax rate (a yellow input cell), tax, total.
- **The reconciliation block.** Two rows: the subtotal as printed on each
  bidder's own document, and the difference against your tabulation. The
  difference row must read zero across every column. Leave it visible in the
  delivered workbook — it is the proof that the transcription is complete.

Use the notes column generously. Every split line, every merged line, every
assumption about what a bidder meant belongs there, next to the number it
affects.

## Sheet 3 — Unit Rates

Effective unit rate = line total ÷ BoQ quantity, by formula from Sheet 2.

Derive it rather than transcribing the bidder's printed rate. Where the two
diverge, the bid contains an arithmetic error and this sheet exposes it.

Add a spread column (highest ÷ lowest). A spread near 1 means the market agrees
on that line. A spread of 3 or 10 means the bidders are pricing different
products, or that the line is a lot rather than a product. Both are worth a
comment in the adjacent column, and both usually become clarification points.

## Sheet 4 — Normalisation

The bridge from as-quoted to like-for-like, one step per row:

```
A  Subtotal ex tax, as quoted          (from the face of each quotation)
B  Arithmetic corrections              (state the error in the basis column)
C  Imputed unpriced scope              (yellow — these are your estimates)
D  Adjusted subtotal                   = A + B + C
E  Tax                                 (at the rate held on Sheet 2)
F  Adjusted total                      = D + E
   Movement vs total as quoted         (negative = overstated; positive = scope left out)
   Adjusted total as % of lowest compliant bid
```

Every adjustment carries a basis in its own column, in plain words: *"four loop
cards at a stated unit rate of 300,000 do not multiply to the line total shown,
and the printed subtotal balances only with the erroneous figure."*

State at the top of the sheet that only two classes of adjustment are permitted
and that scope a bidder *added* is deliberately not adjusted. This pre-empts the
obvious question and shows the discipline was chosen rather than overlooked.

## Sheet 5 — Compliance

Requirements down the rows, bidders across the columns, Yes / No / Partial in
the cells, with a comment column carrying the detail.

Cover: equipment compatibility, all BoQ lines priced, arithmetic reconciles, tax
correctly stated, delivery period, execution programme, warranty, payment terms,
validity stated.

Then a validity block: a yellow reference-date cell, each bid's quote date,
stated validity in days, computed expiry, and a still-valid flag driven by
formula. Making the reference date an input means the client can re-test as the
process drags on.

Then a document-hygiene block, one row per bidder, in prose. Letterheads from
other projects, missing entity names, mislabelled tax, front-loaded payment
terms, scope added quietly. Facts, not verdicts.

## Sheet 6 — Notes & Sources

Numbered notes covering:

- The source pack: every file, what it is, where it came from
- The client requirement and the document it comes from
- Where the quantities came from and whether anyone has verified them
- How line totals were transcribed, and how split lines were handled
- The tax rate applied and confirmation it reproduces each printed total
- **Every imputed value, individually** — what was imputed, for whom, on what
  basis, and an explicit statement that it is your estimate and not a bidder's
  figure
- What was deliberately *not* adjusted, and why
- The reconciliation result
- Any bid excluded from comparison, and the reason
- Technical notes from product research — part numbers verified, capacity
  calculations, variant questions
- Currency, rounding and any exchange rate used
- What this workbook is **not**: name the assessments you did not perform

Write these as full sentences. This sheet is what someone reads when they want
to challenge a number, and it is the difference between a workbook that survives
scrutiny and one that does not.
