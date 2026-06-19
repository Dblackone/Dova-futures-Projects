"""Pre-load the Ibafo swimming-pool project.

Seeds the real figures from the Dova Futures quote (DFL/QT/2026/POOL-001) so a
freshly deployed instance already has the project, its 13 build stages, the cost
breakdown, payment schedule and client-supply materials — ready for both
partners to view and update online.

Idempotent: if the pool project already exists it does nothing, so it is safe to
call on every startup. Set SEED_POOL=0 to disable.
"""

from __future__ import annotations

import os

from . import db

POOL_NAME = "Swimming Pool — Ibafo"

# (name, description, target_date) — dates spread across the ~6–8 week programme.
STAGES: list[tuple[str, str, str]] = [
    ("Excavation & blinding", "Set out, excavate to formation and lay blinding the same day.", "2026-06-21"),
    ("MEP site examination & drain pipe", "M&E site check; lay the main drain pipe.", "2026-06-24"),
    ("Block wall round the pool", '9" blockwork forming the pool surround.', "2026-06-28"),
    ("Felting of wall & blinding", "Waterproof felt / membrane to walls and blinding.", "2026-07-01"),
    ("Reinforcement + MEP pipings", "Fix reinforcement alongside suction/return MEP pipework.", "2026-07-05"),
    ("Casting of floor base", "Cast the reinforced concrete pool base.", "2026-07-08"),
    ("Finishing MEP conduiting", "Complete electrical conduits / MEP first fix.", "2026-07-12"),
    ("Formwork for concrete wall", "Erect marine-board formwork for the pool walls.", "2026-07-15"),
    ("Casting of concrete wall", "Cast the reinforced concrete pool walls.", "2026-07-19"),
    ("Removal of formwork", "Strike formwork once the concrete has cured.", "2026-07-22"),
    ("Plastering of wall", "Render / plaster internal walls and apply waterproofing.", "2026-07-26"),
    ("Tiling", "Lay mosaic tiles to floor, walls and steps; coping band.", "2026-08-02"),
    ("MEP finishing + pump & filtration", "Install sand filter, circulation pump and lights; test & commission.", "2026-08-12"),
]

NOTES: list[tuple[str, str, str]] = [
    ("design", "Pool design summary",
     "Reinforced-concrete pool, 5.0 x 3.6 m internal, depth 1.2-1.8 m (~25.5 m3). "
     "Free-form rectangular plan with one radiused corner, 4-tread corner entry steps, "
     "raised coping band + paved deck and a recessed plant niche. Finish: glass mosaic "
     "tiles over waterproofed render. Sand-filter circulation with underwater lighting."),
    ("general", "Cost breakdown (contract)",
     "Civil works labour N870,000 | Mechanical works N2,340,000 | Electrical works N1,125,000 | "
     "Tiling labour N350,000 | Subtotal N4,685,000 | Contingency 3% N140,550 | "
     "Overheads & profit 10% N468,500 | CONTRACT SUM N5,294,050."),
    ("general", "Payment schedule",
     "60% on mobilization (N3,176,430) | 30% on completion of casting & waterproofing "
     "(N1,588,215) | 10% on completion, testing & handover (N529,405)."),
    ("general", "Owner's budget (expected spend)",
     "Masonry job N650,000 | Carpenter N100,000 | Reinforcement jobs N120,000 | "
     "MEP works N2,000,000 | Tiling works N250,000 | Logistics & miscellaneous N100,000 | "
     "TOTAL EXPECTED N3,220,000. (Your planned outlay by trade, separate from the "
     "contractor's N5,294,050 quote.)"),
    ("general", "Cash plan — 1st client payment",
     "Received N3,000,000. Allocation: profit taken N600,000 | MEP advance N1,400,000 | "
     "civil works settled in full N870,000 (masonry 650k + carpenter 100k + reinforcement "
     "120k) | cash remaining N130,000. Client balance still due N2,294,050."),
    ("material", "Materials to supply (client supply)",
     '9" blocks 350-500 | cement 130-160 bags | marine boards 20 | 2x3 timber 90 lengths | '
     "nails 3 bags | waterproofing powder 1 bag + liquid 1 keg | 10mm rebar 50 + 12mm rebar 50 | "
     "sharp sand, granite, plaster sand and mosaic/coping tiles as required."),
    ("construction", "Optional: felting of pool walls",
     "Waterproof membrane behind the structural walls, recommended where the water table is "
     "high. Lump sum N275,000 - not included in the contract sum unless instructed."),
    ("general", "Commercial terms",
     "Programme ~6-8 weeks from mobilization. Quote valid 30 days (dated 12 Jun 2026). "
     "12-month workmanship warranty on waterproofing. Client supplies all civil materials & "
     "tiles. Contractor: Dova Futures Limited (Ref DFL/QT/2026/POOL-001)."),
]


def maybe_seed() -> None:
    """Seed the pool project unless it already exists or SEED_POOL=0."""
    if os.environ.get("SEED_POOL", "1") == "0":
        return
    if any(p.get("name") == POOL_NAME for p in db.list_projects()):
        return
    seed_pool()


def seed_pool() -> dict:
    project = db.create_project(
        name=POOL_NAME,
        budget=5_294_050,
        currency="₦",
        location="Ibafo, Ogun State",
        description=(
            "Reinforced-concrete swimming pool by Dova Futures Limited. "
            "Budget shown is the contract sum; client-supply materials & tiles are extra. "
            "Ref DFL/QT/2026/POOL-001."
        ),
        start_date="2026-06-19",
        target_end_date="2026-08-14",
    )
    pid = project["id"]
    for name, desc, target in STAGES:
        db.add_milestone(pid, name=name, description=desc, status="not_started", target_date=target)
    for category, title, content in NOTES:
        db.add_note(pid, title=title, content=content, category=category)
    db.add_artisan(
        pid, name="Dova Futures Limited", trade="Pool contractor",
        notes="Main contractor — civil, mechanical, electrical & tiling labour.",
    )
    return project


if __name__ == "__main__":  # allow `python -m server.seed`
    db.init_db()
    if any(p.get("name") == POOL_NAME for p in db.list_projects()):
        print("Pool project already present — nothing to do.")
    else:
        p = seed_pool()
        print(f"Seeded '{p['name']}' (id={p['id']}) with {len(STAGES)} stages.")
