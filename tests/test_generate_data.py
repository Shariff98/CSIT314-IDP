"""The test data generator keeps working (it is also run in CI)."""
import sqlite3

from scripts import generate_data


def test_generator_creates_every_data_type(tmp_path):
    generate_data.main(size=6, db_path=str(tmp_path / "demo.db"), upload_dir=str(tmp_path / "uploads"))
    conn = sqlite3.connect(tmp_path / "demo.db")
    counts = {table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
              for table in ("user_account", "user_profile", "company", "team_member", "category", "idp",
                            "idp_photo", "view_event", "favourite")}
    conn.close()
    assert counts["user_account"] == 14
    assert counts["idp"] == counts["idp_photo"] == 18
    assert counts["company"] == 6
    assert all(counts.values()), counts
