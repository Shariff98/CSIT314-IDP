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
