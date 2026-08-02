---
name: tender-evaluation
description: Evaluate competing vendor quotations against a client's RFP or bill of quantities, and produce the procurement deliverables that follow — a normalised bid comparison workbook, a tender evaluation report, and per-vendor clarification requests. Use this whenever the user has two or more supplier quotes, bids, tenders, proposals or pro-formas for the same scope and wants them compared, normalised, ranked, sanity-checked against market pricing, or queried; whenever they mention an RFP, BoQ, bill of quantities, tender pack, bid tab, vendor selection or contract award; and whenever they ask why one quote is so much higher than another, whether a price is reasonable, or what to ask a vendor before awarding. Applies to any sector — construction, M&E, fire and security systems, IT hardware, facilities, equipment supply. Reach for it even when the user just says "compare these quotes" or sends a folder of supplier PDFs.
---

# Tender evaluation

Comparing bids is easy to do badly. The trap is that a bid tab looks like an
answer — five columns of numbers, one of them lowest — when in fact the columns
usually describe different things. Most of the value in this work comes from
establishing whether the bids are comparable at all, and saying so plainly when
they are not.

The output of a good evaluation is rarely "award to X". More often it is "these
cannot yet be compared, here is precisely why, and here is what to ask."

## The shape of the work

1. Inventory the pack and identify what each document is
2. Transcribe every bid onto the client's own bill of quantities
3. Reconcile your tabulation to each bidder's printed subtotal
4. Check the arithmetic on the face of each bid
5. Normalise to a like-for-like basis
6. Verify prices against independent market data
7. Find the specification defects
8. Analyse soft costs as one pool, not line by line
9. Test compliance against what the client actually asked for
10. Rank — and say what the ranking depends on
11. Draft clarification requests

Steps 1–4 are mechanical and you must not skip them. Steps 5–9 are where the
findings come from. Do not start writing conclusions until step 4 reconciles.

## 1. Inventory the pack

List every document and classify it: client RFP, vendor quotation, company
profile, drawing, correspondence. Note the date on each.

Look at the pack as an artefact in its own right. If it contains one bidder's
marketing profile alongside the competing bids, or the archive is named after
one bidder's proposal title, the client may not have assembled it. Say so — the
client needs to know whether what they handed you is the complete and unaltered
tender. Raise this with the client, never with a vendor.

## 2. Transcribe onto the client's bill of quantities

Build one table whose rows are the client's BoQ lines and whose columns are the
bidders. Not the other way round. Bidders split, merge and reorder lines; the
client's numbering is the only stable spine.

Where a bidder splits one BoQ line across several of its own (detector and
detector base priced separately, say), sum the components into the BoQ line and
record the split in a notes column. Where a bidder prices something the BoQ
never asked for, give it its own row outside the BoQ block — it forms part of
the subtotal they printed, so it cannot simply be dropped, but it is not part of
the tendered scope either.

Transcribe line totals as printed. Do not recompute them yet.

## 3. Reconcile

Add a row that subtracts your tabulated subtotal from the subtotal printed on
each bidder's own document. Every cell must read zero.

This is the single most valuable check in the exercise and it takes a minute.
A non-zero cell means you dropped a line, double-counted one, or misread a
figure — and every downstream conclusion inherits the error. A zero row is also
what lets you tell the client, credibly, that nothing was lost in translation.

## 4. Check the arithmetic

Multiply quantity by unit rate for every line and compare to the line total.
Recompute each subtotal, the tax, and the grand total.

Errors here are common and they matter in a specific way: when a bidder's
printed subtotal only balances *with* the error, the error is load-bearing. That
is different from a typo, and worth stating as such.

## 5. Normalise to like-for-like

Build a visible bridge from as-quoted to comparable. Permit yourself only two
classes of adjustment:

- **Arithmetic corrections** — errors on the face of the bid.
- **Imputed unpriced scope** — BoQ scope a bidder failed to price, valued at the
  median of the bidders who did price it.

Show each adjustment on its own row, attributed, with its basis stated, so the
client can reverse any one of them.

Do not adjust for scope a bidder *added*. Whether the client wants that scope is
the client's decision, and stripping it moves the comparison onto your judgment
rather than the evidence. Show it separately so it can be seen and removed.

Derive effective unit rates by dividing line totals by BoQ quantities. This
surfaces the gap between what a bidder printed as its rate and what it actually
charged.

## 6. Verify against independent market data

Get real prices for as many lines as you can. Local trade listings for the
market the goods will be bought in.

**The mistake to avoid:** converting foreign distributor prices at the spot
exchange rate as a proxy for local cost. On the Ikeja City Mall tender this
overstated commodity devices badly — roughly 50% high on call points, a factor
of 2.3 on loop cards — while landing about right on control panels. The error is
not uniform, so it cannot be corrected with a factor. Use local data, and if you
have already published a conclusion drawn from converted prices, correct it
explicitly rather than quietly.

Label market figures honestly: asking prices from trade sellers indicate the
level of the market, they are not offers capable of acceptance.

Prices far *below* market deserve as much attention as prices above it. A rate
at 27% of market is not a bargain — it usually signals used stock, grey imports,
or a number that will not survive the purchase order.

## 7. Find the specification defects

Read the client's own document critically. Very often the reason bids cannot be
compared is that the client asked ambiguously.

Typical defects, each of which you should quantify:

- A line naming a device *family* rather than a part number, where the family
  contains variants that differ materially in price and performance.
- A line describing a feature (integrated strobe, say) that the bids all price
  as though it were absent — visible when the line sits below a cheaper line in
  every single bid.
- A quantity that ignores what the equipment ships with, or specifies identical
  units where the application actually needs two different part numbers.
- A component specified once where the architecture requires one per panel.

For each defect state the consequence in money and units — "approximately NGN
5.3m turns on this ambiguity, across 20 units" — and the correction. Defects
are the client's to fix, and they are usually cheap to fix.

## 8. Analyse soft costs as one pool

Preliminaries, containment, builders' work, and professional services are all
labour-and-margin lots. Bidders distribute cost between them differently, so
judging any one line in isolation is misleading.

Total them, express the result as a percentage of the equipment value and as a
rate per device or per metre, and rank on the aggregate. On our tender the
bidder with the lowest professional services line — 5.7% — turned out to carry
the second-highest soft cost overall at 23%, because the money sat in
containment and civil works instead. The cost was reclassified, not saved.

Normalised rates are also what let you challenge a price without disclosing
anyone else's: "NGN 1,717 per metre of cable route" is the vendor's own figure
restated, and it is a much harder number to wave away than "high".

Very low soft costs are a risk, not a saving. An allowance that has not been
scoped does not stay cheap; it returns as a variation once the contractor is on
site and competitive tension is gone. Ask bidders below the median to confirm
their price is fixed for all the scope described.

## 9. Test compliance

Build a matrix of the client's stated requirements against each bid: equipment
compatibility, every BoQ line priced, arithmetic, tax correctly stated, delivery
period, programme, warranty, payment terms, validity.

Compute validity against a stated reference date and show which bids have
lapsed. Expired bids are not binding and need written reconfirmation before any
award — this catches people out.

Note document hygiene separately: letterheads referencing an unrelated project,
a vendor name absent from the document's text layer, mislabelled tax rates. None
of these are disqualifying on their own, but together they indicate how much
care went into the submission.

**Look hard for the non-price discriminator.** On our tender it was manufacturer
certification: the panel's commissioning software is restricted to certified
engineers, so without one the system cannot be lawfully programmed, tested or
certificated regardless of what was paid for the hardware. No bid addressed it,
and it mattered more than any price finding. Most technical procurements have
something of this kind — a licence, an accreditation, a support entitlement.
Find it and make it a condition of award.

## 10. Rank, and state what the ranking rests on

Rank only the compliant bids, on the adjusted figures, and show the premium over
the lowest.

Exclude a non-compliant bid from the ranking rather than burying it — a bid
offering different equipment is not a discount on the tendered work, it is a
price for a different project. Say that plainly.

Label a preliminary ranking as preliminary and list what must happen before it
can be relied on. Rankings drawn from incomplete information change once
clarifications come back, and a client who was not warned of that will feel
misled.

Record your assumptions where they are visible, not in a footnote. If the whole
evaluation rests on an unverified premise — "it has been assumed that the
existing panel is unserviceable; this is a stated assumption, not a finding of
this review" — put it in section 1 so any later reader can see what to revisit.

State the limitations honestly: what you did not inspect, verify, or assess.

## 11. Clarification requests

See `references/clarification-requests.md` for the full structure. The essentials:

Each vendor gets a **general section**, worded identically across all vendors,
and a **vendor-specific section** drawn from their own submission. Keep any
points you found that the client did not ask for in a **third section, clearly
marked optional**, so the client can include or drop each one — it is their
correspondence, not yours.

**Never disclose one vendor's pricing to another.** Anchor every price challenge
either to independently verified market data or to the vendor's own figure
restated as a normalised rate. This is not only fair, it is more effective: a
vendor can dismiss "higher than others" and cannot dismiss "NGN 9,815 per
device".

Where the client's own document already required something no bidder supplied —
a condition survey, a technical assessment — ask for it as compliance with an
existing obligation rather than as new work. That is a much stronger position.

## Deliverables and how to build them

Three artefacts, in this order:

| Artefact | Format | Reference |
|---|---|---|
| Bid comparison workbook | `.xlsx` | `references/bid-workbook.md` |
| Tender evaluation report | `.docx` | `references/evaluation-report.md` |
| Per-vendor clarification requests | `.docx` each | `references/clarification-requests.md` |

Build the workbook first — the report quotes it, and the clarification requests
quote the report.

**Reading source documents.** `pypdf` for PDFs, `python-docx` for Word,
`openpyxl` for spreadsheets. Install as needed; none are guaranteed present.

**Writing Word documents.** Use `scripts/build_document.js`, which wraps the
`docx` npm package with the heading, body and bullet primitives these documents
need. Writing five near-identical documents by hand invites drift between them;
a shared builder keeps them consistent. Run `npm install docx` first if the
require fails.

**Verifying output.** LibreOffice is often unavailable or broken in sandboxes,
so a render-and-look check may not be possible. When it is not, validate
structurally instead: run the XSD validator if you have one, then read the text
back out of the file with `python-docx` and check every heading and bullet
landed. Tell the user you could not view it and suggest they open it once.

## Working with the client

Procurement work carries decisions the client owns and you do not: how much
scope to challenge, whether to include a finding in correspondence, whether a
vendor stays in the running. Surface those as choices with a recommendation
attached, and then do what they decide.

When a client edits your draft and hands it back, treat their version as the
approved text. Reproduce it faithfully. If something material was dropped —
a price challenge, a double-counting safeguard — say so once, explain what the
omission lets the vendor do, and let them decide. Do not reinstate it silently
and do not raise it twice.

Watch for requests that will backfire in a way the client has not seen. Asking
every vendor to express professional services as a percentage of the contract
value pushes four prices down and one *up*, if that one has already hidden its
margin in the containment and civil works lines. Flag that before the letters go
out, not after the revised quotes arrive.
