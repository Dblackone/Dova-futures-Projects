# Clarification requests

One document per vendor, plus one covering email used for all of them.

These go to outside parties. Everything else you produce is internal; this is
not. Write accordingly.

## Draft before you format

Produce the drafts as a single reviewable markdown file first, with all vendors
in it, and get the client's approval before building any document. Clients edit
these heavily — wording, which challenges to keep, how hard to push. Formatting
five Word documents before the text is settled wastes the work twice.

Present the general section once in chat, note that it appears verbatim in each
draft, and then show each vendor's specific section in full. Repeating the
general section five times in a chat message buries the part they need to read.

## Structure of each document

| Section | Content |
|---|---|
| A | General requirements — identical wording across every vendor |
| B | Vendor-specific clarifications, from their own submission |
| C | Additional points you found, clearly marked optional |

Section C is the one that earns trust. These are real findings the client did
not ask you to raise, and keeping them separate means the client chooses their
own posture rather than discovering later that you escalated on their behalf.
Add a short table in your covering note naming the single highest-value optional
point per vendor, so a client who wants only one knows which.

## Section A — what belongs in it

Anything you would ask every vendor. Typically:

- Re-submit a revised quotation for the entire scope, superseding the original
- Price every BoQ line; address in writing any line considered unnecessary
- Full product identification per item: model, product code, manufacturer
  reference, technical specification, variant, and anything else that pins down
  the exact item
- A technical assessment report on the existing installation
- The contents that report must cover
- The exact specification and variation of all equipment
- Any line where you need every vendor's engineering position, whether or not
  they priced it
- Professional services expressed as a percentage of the other items, with a
  build-up
- Certification and competence to support the platform proposed

Word it identically in every copy. Vendors talk to each other; identical
wording is what makes "this is being asked of everyone" verifiable rather than
merely asserted.

## Section B — what belongs in it

Only what arises from that vendor's own submission, referenced to BoQ item
numbers so their commercial team can route it internally without translation.

## The pricing rule

**Never disclose one vendor's pricing to another.** Not the range, not the
median, not "others quoted less".

Anchor every price challenge to one of two things:

1. **Independently verified market data** — *"stands materially above verified
   market pricing for a panel of this description, which sits in the region of
   NGN 4.5m to NGN 4.9m."*
2. **The vendor's own figure restated as a normalised rate** — *"NGN 5,300,000
   equates to approximately NGN 9,815 per device installed."*

The second is the more powerful of the two, and it costs you nothing to compute.
The vendor cannot dispute the arithmetic, cannot claim you compared them to
someone cheaper, and has to engage with what the work actually costs.

## Tone

Firm, specific, not adversarial. These vendors may end up holding the contract.

- Open by confirming the submission is still under consideration, where true.
- Credit what is genuinely good. *"Yours was the only submission to state actual
  manufacturer part numbers, which is to your credit."* It costs nothing and the
  harder questions land better after it.
- Frame anything the RFP already required as compliance, not as new work.
- Close with the deadline, the return address, what to do if a point cannot be
  answered in time, and the consequence of not responding.

## The covering email

One body for all vendors, with only the vendor name, contact, their quotation
date, and the attachment changing. It should:

- Reference their quotation by date
- Point to the attached document and explain its two-part structure
- List what must come back: revised quotation, technical report, written
  responses to Section B in order
- State the validity period required on the revised quotation
- Say the request is going to every vendor, that it exists to put all
  submissions on a comparable basis, and that theirs remains under consideration
- Give the deadline, the return address, and a contact for questions

Use the **same deadline for every vendor**. A vendor who learns another had
longer has a fair complaint, and it undercuts the fairness paragraph you just
wrote.

Check the fairness paragraph is true for each recipient before it goes out. If
the client is not in fact prepared to consider a re-quote from one vendor, that
sentence must come out of their copy. Telling a vendor they are live when they
are not costs nothing now and credibility later.

## Building the documents

Use `scripts/build_document.js`. One script per vendor, sharing the primitives,
so the general section cannot drift between copies.

Reproduce the client's approved text exactly. Fix only genuine typography — a
missing full stop, a straight apostrophe where the document uses curly. Do not
improve their wording.

When the client's edits have introduced inconsistencies between vendors — one
document's heading differing from another's, a lead-in sentence present in three
copies and absent from two — build what they sent, then note the difference in a
short table afterwards and offer to align. They may have done it deliberately.

Verify every document before delivery: validate it, then read the text back out
and confirm every heading and bullet is present. If you could not render it to
look at, say so and suggest they open one.
