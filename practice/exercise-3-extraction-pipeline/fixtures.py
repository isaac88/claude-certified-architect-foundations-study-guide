"""Synthetic document corpus for exercise 3. EVERY document here is invented.

Ten supplier documents in ten layouts, plus the gold answers the pipeline
scores against. No organisation, figure, VAT number, bank account or
reference on this page belongs to anyone real (`example.com` throughout);
none of the numbers is a fact about the world — they exist so the extraction
run has something deterministic to be right or wrong about.

The corpus is built around the traps 4.3 and 4.4 name:

* a **blank PO box** (`scan-05`) — the field is absent from the source, so a
  required non-nullable `po_number` would make invention the only legal
  output;
* a **stated total that disagrees with its own line items** (`inv-03`) —
  `conflict_detected`, never a quietly corrected number;
* two documents that are **none of the enumerated types** (`oth-06`,
  `oth-10`) — `other` + freeform detail, not a new enum value;
* documents where payment is **not stated at all** (`oth-06`, `cn-07`,
  `oth-10`) — `unclear`, not a guess;
* dates in five formats and amounts in two decimal conventions — the prompt
  coerces, the schema only types.

`FEW_SHOT_EXAMPLES` are three *different* invented documents (never corpus
documents — that would be leakage). They cover three layouts: the email
receipt, the OCR-scanned invoice with a blank box, and the delivery note.
Layouts deliberately NOT covered by any example: the credit note, the
European-decimal invoice and the bank statement — those are where the
"does few-shot generalise?" measurement happens.
"""

# --------------------------------------------------------------------------
# The corpus
# --------------------------------------------------------------------------

DOCUMENTS = [
    {
        "id": "inv-01",
        "layout": "plain invoice, ISO dates, VAT line",
        "covered_by_example": False,
        "text": """\
NORTHGATE SUPPLIES LTD
14 Harbour Road, Bristol BS1 5TY
VAT registration: GB 418 2290 11

INVOICE
Invoice number: NG-4471
Issue date: 2025-01-14
Due date: 2025-02-13
Purchase order: PO-88213
Bill to: Larkfield Joinery

Description                      Qty    Unit     Amount
Oak veneer sheet 2440x1220         6   48.00     288.00
Birch ply 18mm                     4   31.50     126.00
Delivery                           1   35.00      35.00

Subtotal                                         449.00
VAT 20%                                           89.80
Total due GBP                                    538.80

Payment not yet received. Terms: 30 days.
""",
        "gold": {
            "document_type": "invoice",
            "document_id": "NG-4471",
            "issue_date": "2025-01-14",
            "vendor_name": "Northgate Supplies Ltd",
            "vendor_tax_id": "GB 418 2290 11",
            "po_number": "PO-88213",
            "currency": "GBP",
            "line_item_count": 3,
            "stated_total": 538.80,
            "payment_status": "unpaid",
            "conflict_detected": False,
        },
    },
    {
        "id": "inv-02",
        "layout": "ASCII table, UK slash date, PO box says '(none supplied)'",
        "covered_by_example": False,
        "text": """\
=========================================================
  BLUEFORGE METALS                              invoice
=========================================================
  Ref .............. BF/2024/0912
  Dated ............ 31/12/2024
  Terms ............ net 30
  Customer ......... Tamar Marine Ltd
  PO ............... (none supplied)
---------------------------------------------------------
  ITEM                          QTY     RATE      LINE
  Stainless rod 316 12mm         20     9.40    188.00
  Cutting charge                  1    24.00     24.00
  Carriage                        1    18.50     18.50
---------------------------------------------------------
  NET 230.50  |  VAT (0%) 0.00  |  TOTAL DUE GBP 230.50
  Awaiting payment.
=========================================================
""",
        "gold": {
            "document_type": "invoice",
            "document_id": "BF/2024/0912",
            "issue_date": "2024-12-31",
            "vendor_name": "Blueforge Metals",
            "vendor_tax_id": None,
            "po_number": None,
            "currency": "GBP",
            "line_item_count": 3,
            "stated_total": 230.50,
            "payment_status": "unpaid",
            "conflict_detected": False,
        },
    },
    {
        "id": "inv-03",
        "layout": "prose invoice, long-form date, TOTAL disagrees with its own lines",
        "covered_by_example": False,
        "text": """\
Harlow & Finch Consulting
Invoice INV-2025-0033
Date: 5 March 2025
Client: Denton Rail Group
Purchase order: 4409-DRG

  Discovery workshop (2 days)                  1,600.00
  Interview transcription                        240.00
  Report production                              180.00

  Subtotal                                     2,020.00
  VAT @ 20%                                      404.00
  TOTAL                                        2,484.00

Payable on receipt. Not yet settled.
""",
        "gold": {
            "document_type": "invoice",
            "document_id": "INV-2025-0033",
            "issue_date": "2025-03-05",
            "vendor_name": "Harlow & Finch Consulting",
            "vendor_tax_id": None,
            "po_number": "4409-DRG",
            "currency": "GBP",
            "line_item_count": 3,
            "stated_total": 2484.00,
            "payment_status": "unpaid",
            # 1600 + 240 + 180 + 404 VAT = 2424.00, the document says 2484.00.
            "conflict_detected": True,
        },
    },
    {
        "id": "rcp-04",
        "layout": "email body receipt, no field labels",
        "covered_by_example": True,
        "text": """\
From: orders@brambleroast.example.com
To: priya.n@example.com
Subject: Thanks for your order, Priya

Hi Priya,

Your order is on its way. Here is what you paid for on Dec 3, 2024:

  2 x Ethiopia Guji 250g ................ 19.00
  1 x Colombia Huila 1kg ................ 26.50
  Shipping .............................. 3.95

Paid in full by card ending 4417 - total GBP 49.45.
Order reference BR-99118.

Bramble Roast Coffee, 8 Mill Lane, Exeter
""",
        "gold": {
            "document_type": "receipt",
            "document_id": "BR-99118",
            "issue_date": "2024-12-03",
            "vendor_name": "Bramble Roast Coffee",
            "vendor_tax_id": None,
            "po_number": None,
            "currency": "GBP",
            "line_item_count": 3,
            "stated_total": 49.45,
            "payment_status": "paid",
            "conflict_detected": False,
        },
    },
    {
        "id": "scan-05",
        "layout": "OCR-scanned invoice, letter noise, EMPTY PO box",
        "covered_by_example": True,
        "text": """\
 MERlDlAN  FASTENERS          (scanned copy - page 1 of 1)
 ----------------------------------------------------------
 lNVOlCE No:   MF-7102
 Date:         09 Apr 2025
 P.O. Number:  [                              ]
 Account:      MER-0042
 Cust:         Ravenhill Engineering

 M8 hex bolt zinc      x500                      125.00
 Nyloc nut M8          x500                       62.50
 Washer form A M8      x500                       21.00
 ----------------------------------------------------------
 Goods                                           208.50
 VAT 20%                                          41.70
 TOTAL GBP                                       250.20
 ----------------------------------------------------------
 Remittance overdue - second reminder.
""",
        "gold": {
            "document_type": "invoice",
            "document_id": "MF-7102",
            "issue_date": "2025-04-09",
            "vendor_name": "Meridian Fasteners",
            "vendor_tax_id": None,
            # The box is on the page and it is EMPTY. null is the only
            # honest answer; "[ ]", "N/A" and an invented number are all
            # wrong, and a required non-nullable field permits none of them.
            "po_number": None,
            "currency": "GBP",
            "line_item_count": 3,
            "stated_total": 250.20,
            "payment_status": "unpaid",
            "conflict_detected": False,
        },
    },
    {
        "id": "oth-06",
        "layout": "delivery note - not an enumerated type, no money at all",
        "covered_by_example": True,
        "text": """\
ASHBY LOGISTICS - DELIVERY NOTE
Note no: DN-55120           Despatched: 22/01/2025
Consignee: Keldon Brewing Co
Carrier: Overnight Freight

  4 x pallet, malt (25kg sacks x40)
  1 x pallet, hops (vacuum packed)

No charge on this note - goods are invoiced separately under INV-KB-3390.
Signed on receipt: ..............................
""",
        "gold": {
            "document_type": "other",
            "document_id": "DN-55120",
            "issue_date": "2025-01-22",
            "vendor_name": "Ashby Logistics",
            "vendor_tax_id": None,
            "po_number": None,
            "currency": "unclear",
            "line_item_count": 2,
            "stated_total": None,
            "payment_status": "unclear",
            "conflict_detected": False,
        },
    },
    {
        "id": "cn-07",
        "layout": "credit note, negative amounts, one positive fee",
        "covered_by_example": False,
        "text": """\
VALE PACKAGING LTD                          CREDIT NOTE
Credit note: CN-2025-018    Against invoice: VP-7742
Issued: 2025-02-02
Customer: Harrow Foods

  Return: 3 x carton 300x200x150 @ 4.20            -12.60
  Return: 1 x tape roll (damaged)                   -3.10
  Restocking fee                                    +2.00

  Credit total GBP                                 -13.70

To be offset against the next statement.
""",
        "gold": {
            "document_type": "credit_note",
            "document_id": "CN-2025-018",
            "issue_date": "2025-02-02",
            "vendor_name": "Vale Packaging Ltd",
            "vendor_tax_id": None,
            "po_number": None,
            "currency": "GBP",
            "line_item_count": 3,
            "stated_total": -13.70,
            "payment_status": "unclear",
            "conflict_detected": False,
        },
    },
    {
        "id": "inv-08",
        "layout": "European decimals (comma + space), sparse: no tax id, no PO",
        "covered_by_example": False,
        "text": """\
Studio Lindqvist AB
Faktura / Invoice  SL-0291
2025-05-20

To: Merrow Interiors

  Concept development, 12 h                     960,00
  Revision round                                180,00

  Total EUR                                   1 140,00

Payment within 14 days. Reverse charge - VAT not applied.
""",
        "gold": {
            "document_type": "invoice",
            "document_id": "SL-0291",
            "issue_date": "2025-05-20",
            "vendor_name": "Studio Lindqvist AB",
            "vendor_tax_id": None,
            "po_number": None,
            "currency": "EUR",
            "line_item_count": 2,
            "stated_total": 1140.00,
            "payment_status": "unpaid",
            "conflict_detected": False,
        },
    },
    {
        "id": "rcp-09",
        "layout": "till receipt, two-digit year, cash and change lines",
        "covered_by_example": False,
        "text": """\
        THE OLD FORGE CAFE
        Market Sq, Ludlow
        --------------------
        03 Dec 24     12:41
        --------------------
        Flat white       3.40
        Sourdough toast  5.20
        Jam (extra)      0.60
        --------------------
        TOTAL          GBP 9.20
        CASH           GBP 10.00
        CHANGE         GBP 0.80
        --------------------
        Receipt 0074-118
        No VAT receipt issued
""",
        "gold": {
            "document_type": "receipt",
            "document_id": "0074-118",
            "issue_date": "2024-12-03",
            "vendor_name": "The Old Forge Cafe",
            "vendor_tax_id": None,
            "po_number": None,
            "currency": "GBP",
            # CASH and CHANGE are tender lines, not goods lines.
            "line_item_count": 3,
            "stated_total": 9.20,
            "payment_status": "paid",
            "conflict_detected": False,
        },
    },
    {
        "id": "oth-10",
        "layout": "bank statement extract - other, and no document total at all",
        "covered_by_example": False,
        "text": """\
CALDER BANK - STATEMENT EXTRACT
Account 20-44-19 / 30119827      Period: 01/04/2025 - 30/04/2025

  04/04/2025  CARD PAYMENT   NORTHGATE SUPPLIES      GBP -538.80
  11/04/2025  TRANSFER IN    DENTON RAIL GROUP       GBP +2,484.00

  Closing balance 30/04/2025                         GBP 4,915.60
""",
        "gold": {
            "document_type": "other",
            "document_id": None,
            # The document states a period, not an issue date.
            "issue_date": None,
            "vendor_name": "Calder Bank",
            "vendor_tax_id": None,
            "po_number": None,
            "currency": "GBP",
            "line_item_count": 2,
            # A closing balance is not a total payable or paid.
            "stated_total": None,
            "payment_status": "unclear",
            "conflict_detected": False,
        },
    },
]

# Fields scored against gold. Everything here is objective on the page.
SCORED_FIELDS = [
    "document_type",
    "document_id",
    "issue_date",
    "vendor_name",
    "vendor_tax_id",
    "po_number",
    "currency",
    "line_item_count",
    "stated_total",
    "payment_status",
    "conflict_detected",
]

# --------------------------------------------------------------------------
# Few-shot examples (4.2): three layouts, each with a REASON line
# --------------------------------------------------------------------------
# None of these is a corpus document. Each carries the reasoning that
# generalises - why this handling beat the plausible alternative - because
# bare input/output pairs only teach the three layouts shown.

FEW_SHOT_EXAMPLES = [
    {
        "label": "email receipt",
        "document": """\
From: shop@penrose-stationery.example.com
Subject: Your order is confirmed

Morning Tom,

Charged to your card today, 14 Feb 2025:

  1 x A5 notebook, ruled ............ 8.40
  3 x fineliner black ............... 5.70
  Postage ........................... 2.95

Total taken GBP 17.05. Order PS-20411.

Penrose Stationery, Unit 4, Leeds
""",
        "record": {
            "document_type": "receipt",
            "document_type_detail": None,
            "document_id": "PS-20411",
            "issue_date": "2025-02-14",
            "vendor_name": "Penrose Stationery",
            "vendor_tax_id": None,
            "po_number": None,
            "currency": "GBP",
            "line_items": [
                {"description": "A5 notebook, ruled", "amount": 8.40},
                {"description": "fineliner black", "amount": 5.70},
                {"description": "Postage", "amount": 2.95},
            ],
            "subtotal": None,
            "tax_amount": None,
            "stated_total": 17.05,
            "calculated_total": 17.05,
            "conflict_detected": False,
            "conflict_note": None,
            "payment_status": "paid",
        },
        "reasoning": (
            "Receipt, not invoice: money has already changed hands "
            "(\"charged to your card today\"), so payment_status is paid and "
            "nothing is owed. The prose carries no field labels, so the "
            "order reference is the document_id and the sender's sign-off is "
            "the vendor - not the subject line. Postage is a charged line "
            "like any other. There is no tax line and no PO, so those are "
            "null rather than 0.00 or a guess."
        ),
    },
    {
        "label": "OCR-scanned invoice with an empty box",
        "document": """\
 KlNGSLEY  ABRASlVES         (scan)
 ------------------------------------------------
 lnvoice:     KA-3318
 Dated:       17 Jun 2025
 Order ref:   [                        ]
 Client:      Weybridge Tooling

 Flap disc 115mm  x40                      96.00
 Wire cup brush   x6                       41.40
 ------------------------------------------------
 Goods                                    137.40
 VAT 20%                                   27.48
 TOTAL GBP                                164.88
 Payment outstanding.
""",
        "record": {
            "document_type": "invoice",
            "document_type_detail": None,
            "document_id": "KA-3318",
            "issue_date": "2025-06-17",
            "vendor_name": "Kingsley Abrasives",
            "vendor_tax_id": None,
            "po_number": None,
            "currency": "GBP",
            "line_items": [
                {"description": "Flap disc 115mm x40", "amount": 96.00},
                {"description": "Wire cup brush x6", "amount": 41.40},
            ],
            "subtotal": 137.40,
            "tax_amount": 27.48,
            "stated_total": 164.88,
            "calculated_total": 164.88,
            "conflict_detected": False,
            "conflict_note": None,
            "payment_status": "unpaid",
        },
        "reasoning": (
            "The order-ref box is printed but empty, so po_number is null. "
            "Null is the only honest value: \"[ ]\", \"N/A\" and a plausible "
            "invented reference all assert something the page does not say, "
            "and a downstream system cannot tell an invented reference from "
            "a real one. Scanner noise is in the letters only (l for I), so "
            "the vendor name is read through the noise and \"(scan)\" is a "
            "page annotation, not part of the name. Goods + VAT equals the "
            "printed total, so there is no conflict to flag."
        ),
    },
    {
        "label": "delivery note - an unenumerated type",
        "document": """\
FENWORTH HAULAGE - GOODS DESPATCH NOTE
Despatch no: GD-7781        Date: 08/03/2025
Deliver to: Marlow Ceramics

  6 x crate, glaze (5L tubs x4)
  2 x crate, kiln furniture

Carriage paid by sender. No charge on this note.
""",
        "record": {
            "document_type": "other",
            "document_type_detail": "goods despatch note",
            "document_id": "GD-7781",
            "issue_date": "2025-03-08",
            "vendor_name": "Fenworth Haulage",
            "vendor_tax_id": None,
            "po_number": None,
            "currency": "unclear",
            "line_items": [
                {"description": "crate, glaze (5L tubs x4)", "amount": None},
                {"description": "crate, kiln furniture", "amount": None},
            ],
            "subtotal": None,
            "tax_amount": None,
            "stated_total": None,
            "calculated_total": None,
            "conflict_detected": False,
            "conflict_note": None,
            "payment_status": "unclear",
        },
        "reasoning": (
            "A despatch note is none of invoice, receipt, credit_note or "
            "purchase_order, so it is other plus a freeform detail naming "
            "what the document calls itself. It does not get a new enum "
            "value: the enum is the contract every consumer already parses, "
            "and one unknown type does not justify changing it. The note "
            "carries goods but no prices, so line amounts, totals and "
            "currency are null or unclear, and payment_status is unclear - "
            "the page says nothing about payment, which is not the same as "
            "saying it is unpaid."
        ),
    },
]
