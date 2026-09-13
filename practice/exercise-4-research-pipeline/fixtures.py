"""Synthetic corpus for exercise 4. EVERY source here is invented.

Organisations, figures and URLs are fictional (example.org) so the lab can
have a deterministic timeout and a deliberate two-figure conflict without
attributing made-up numbers to anyone real. The shape of each entry is the
5.6 claim-source mapping minus the claim: url, title, excerpt, date.
"""

import math
import re

# The two figures the conflict fixture plants (5.6): same metric, two
# credible sources, two dates. Synthesis must show BOTH, never one or a mean.
CONFLICT_FIGURES = ("3.5 GW", "4.0 GW")

WEB = [
    {
        "id": "web-1",
        "url": "https://example.org/egc/market-report-2022",
        "title": "European Geothermal Council — Geothermal Market Report 2022",
        "date": "2023-02-14",
        "excerpt": (
            "Installed geothermal electricity capacity in Europe reached 3.5 GW "
            "at the end of 2022, with 142 plants in operation. Growth was "
            "concentrated in Türkiye, Italy and Iceland."
        ),
        "keywords": "geothermal electricity power capacity installed GW europe growth plants 2022 market",
    },
    {
        "id": "web-2",
        "url": "https://example.org/grsa/renewable-capacity-statistics-2025",
        "title": "Global Renewables Statistics Agency — Renewable Capacity Statistics 2025",
        "date": "2025-03-27",
        "excerpt": (
            "Europe's geothermal power capacity stood at 4.0 GW at end-2024, "
            "up 4% year on year. Geothermal remains under 1% of the region's "
            "renewable electricity capacity."
        ),
        "keywords": "geothermal electricity power capacity installed GW europe growth statistics 2024 2025 percent share",
    },
    {
        "id": "web-3",
        "url": "https://example.org/eu-energy/geothermal-strategy-call",
        "title": "EU energy portal — Parliament calls for a European geothermal strategy",
        "date": "2024-01-18",
        "excerpt": (
            "The European Parliament adopted a resolution calling on the "
            "Commission to table an EU geothermal strategy, citing permitting "
            "delays of five to seven years as the main barrier to deployment."
        ),
        "keywords": "geothermal policy strategy europe EU parliament permitting barrier regulation deployment 2024",
    },
    {
        "id": "web-4",
        "url": "https://example.org/energy-wire/heat-pump-sales-2024",
        "title": "EnergyWire — Geothermal heat pump sales in Europe fall 9% in 2024",
        "date": "2024-11-05",
        "excerpt": (
            "Sales of ground-source (geothermal) heat pumps in Europe fell 9% "
            "in 2024 after two years of double-digit growth, as subsidy schemes "
            "were cut in Germany and Italy."
        ),
        "keywords": "geothermal heat pump sales europe growth decline subsidy market 2024 heating",
    },
]

# The journal corpus is the flaky source. All four abstracts share the broad
# terms, so a broad policy query matches all four and TIMES OUT after two
# (see JOURNAL_TIMEOUT_AFTER); a narrowed query matches one or two and works.
JOURNAL = [
    {
        "id": "jnl-1",
        "url": "https://example.org/journal/geo-policy/permitting-bottlenecks",
        "title": "Permitting bottlenecks for geothermal power in Europe: a 12-country review",
        "date": "2024-06-01",
        "excerpt": (
            "Across twelve European countries the median time from exploration "
            "licence to plant commissioning was 6.5 years; permitting, not "
            "resource risk, was the binding constraint on geothermal policy."
        ),
        "keywords": "geothermal policy europe permitting licence regulation review countries",
    },
    {
        "id": "jnl-2",
        "url": "https://example.org/journal/geo-policy/subsidy-design",
        "title": "Subsidy design and geothermal district heating uptake in Europe",
        "date": "2023-09-12",
        "excerpt": (
            "Capital subsidies covering at least 30% of drilling cost doubled "
            "geothermal district heating project starts in the European "
            "municipalities studied; operating subsidies had no measurable effect."
        ),
        "keywords": "geothermal policy europe subsidy district heating drilling incentive",
    },
    {
        "id": "jnl-3",
        "url": "https://example.org/journal/geo-policy/risk-insurance",
        "title": "Geological risk insurance schemes as geothermal policy instruments in Europe",
        "date": "2022-11-30",
        "excerpt": (
            "Public geological risk insurance in four European countries raised "
            "the share of exploratory wells drilled by non-utility developers "
            "from 12% to 31% within five years."
        ),
        "keywords": "geothermal policy europe risk insurance exploration wells developers",
    },
    {
        "id": "jnl-4",
        "url": "https://example.org/journal/geo-policy/eu-strategy-gap",
        "title": "The missing EU geothermal strategy: a policy gap analysis",
        "date": "2024-03-08",
        "excerpt": (
            "Unlike wind and solar, geothermal has no dedicated EU-level "
            "strategy; the paper maps 23 instruments across member states and "
            "finds no coordination of targets or reporting for European geothermal policy."
        ),
        "keywords": "geothermal policy europe EU strategy gap analysis coordination targets",
    },
]

JOURNAL_TIMEOUT_AFTER = 2

# The journal API is also flaky: the FIRST call of a run times out after one
# abstract whatever the query (a transient, 5.3 — retrying the same query
# recovers it). Broad queries (> JOURNAL_TIMEOUT_AFTER hits) always time out.
_journal_calls = 0


def reset() -> None:
    global _journal_calls
    _journal_calls = 0

# Local documents the document spoke can read. Longer than a search hit, so
# the extraction spoke must quote a verbatim excerpt rather than get one free.
DOCUMENTS = {
    "doc-egc-heating-2024": {
        "title": "European Geothermal Council — Geothermal Heating and Cooling Outlook 2024",
        "url": "local://doc-egc-heating-2024",
        "date": "2024-06-20",
        "text": (
            "Executive summary. Geothermal district heating in Europe reached 412 "
            "systems in operation at the end of 2023, with a further 300 projects "
            "under development. France, Germany and the Netherlands account for "
            "most new capacity. The outlook estimates that district heating could "
            "supply 25% of Europe's heat demand by 2040 if drilling costs fall by "
            "a third.\n\nMarket barriers. Respondents in the council's survey rank "
            "permitting time first and geological risk second; access to capital "
            "ranks third. Only six countries operate a public risk-insurance "
            "scheme.\n\nMethodology. Figures are compiled from national "
            "associations and cross-checked against operator reporting; systems "
            "under 0.5 MWth are excluded."
        ),
    },
}

_STOP = {
    "the", "and", "for", "with", "from", "into", "what", "how", "are", "is",
    "of", "in", "on", "to", "a", "an", "by", "at", "or", "vs", "recent",
    "current", "latest", "state", "status", "overview",
}


class SimulatedTimeout(Exception):
    """The journal API died mid-response. Carries what came back before it did."""

    def __init__(self, partials: list[dict], matched: int, query: str):
        super().__init__(f"journal search timed out after {len(partials)} of {matched} results")
        self.partials = partials
        self.matched = matched
        self.query = query


def _terms(query: str) -> list[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9-]+|\d{4}", query.lower())
    return [w for w in words if w not in _STOP and len(w) >= 2]


def _matches(term: str, source: dict) -> bool:
    # prefix match on the first five letters: europe/european, permit/permitting
    stem = term[:5]
    haystack = f"{source['title']} {source['excerpt']} {source['keywords']}".lower()
    return any(w.startswith(stem) for w in re.findall(r"[a-z0-9-]+", haystack))


def search(query: str, corpus: str) -> list[dict]:
    """Deterministic keyword search.

    Terms every source in the corpus shares ("geothermal", "Europe") carry no
    information, so they are ignored when at least one DISTINCTIVE term
    matches something; a source is a hit when it matches at least a third of
    the distinctive terms (a query spanning three sub-topics still finds
    each of them). A query made only of shared terms is broad: the whole
    corpus matches. An empty list is a VALID EMPTY: the corpus was reached
    and holds nothing on the query.
    """
    pool = {"web": WEB, "journal": JOURNAL}[corpus]
    matched = {t: {s["id"] for s in pool if _matches(t, s)} for t in _terms(query)}
    distinctive = [t for t, ids in matched.items() if 0 < len(ids) < len(pool)]
    generic = [t for t, ids in matched.items() if len(ids) == len(pool)]
    if distinctive:
        need = math.ceil(len(distinctive) / 3)
        hits = [s for s in pool if sum(s["id"] in matched[t] for t in distinctive) >= need]
    elif generic:
        hits = list(pool)
    else:
        hits = []
    hits = [{k: v for k, v in s.items() if k != "keywords"} for s in hits]
    if corpus == "journal":
        global _journal_calls
        _journal_calls += 1
        if len(hits) > JOURNAL_TIMEOUT_AFTER:
            raise SimulatedTimeout(hits[:JOURNAL_TIMEOUT_AFTER], len(hits), query)
        if _journal_calls == 1 and hits:
            raise SimulatedTimeout(hits[:1], len(hits), query)
    return hits
