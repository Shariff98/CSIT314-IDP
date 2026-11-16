"""The seed data must give the budget chatbot real choices."""
from entity.idp import IDP
from scripts import generate_data


def test_budgets_cluster_where_customers_ask(tmp_path):
    generate_data.main(size=40, db_path=str(tmp_path / "demo.db"), upload_dir=str(tmp_path / "uploads"))
    assert len(IDP.find_in_budget(9_000, 13_000)) >= 5


def test_clustered_budget_stays_in_range():
    import random
    rng = random.Random(1)
    budgets = [generate_data.clustered_budget(rng) for _ in range(500)]
    assert all(5_000 <= b <= 120_000 for b in budgets)
    assert sum(8_000 <= b <= 14_000 for b in budgets) > len(budgets) * 0.3


def test_demo_has_enough_everyday_rooms_and_searchable_descriptions(tmp_path):
    # The hosted demo runs the generator with --size 20.
    generate_data.main(size=20, db_path=str(tmp_path / "demo.db"), upload_dir=str(tmp_path / "uploads"))
    projects = IDP.find_in_budget(0, 10_000_000)
    assert sum(p.category == "Kitchen" for p in projects) >= 5
    descriptions = {p.description for p in projects}
    assert len(descriptions) > len(projects) * 0.8 and all("featuring" in d for d in descriptions)
    assert any("storage" in d for d in descriptions)
