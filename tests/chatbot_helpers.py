"""Helpers for the budget chatbot tests: a fake LLM and quick ways to create designers and projects."""
from control.recommend_idps_controller import LLMUnavailable
from entity.company import Company
from entity.db import get_connection
from entity.idp import IDP
from entity.user_account import UserAccount


class FakeLLMGateway:
    """Stands in for LLMGateway. Set .prefs / .reply, or .fail to simulate an outage."""

    def __init__(self, prefs=None, reply=None, fail=False, fail_reply=False):
        self.prefs, self.reply, self.fail, self.fail_reply = prefs or {}, reply, fail, fail_reply
        self.calls = []

    def extract_preferences(self, message, history, categories, styles):
        self.calls.append(("extract", message))
        if self.fail:
            raise LLMUnavailable("simulated outage")
        return dict(self.prefs)

    def write_reply(self, message, projects, notes):
        self.calls.append(("reply", [p["id"] for p in projects]))
        if self.fail or self.fail_reply:
            raise LLMUnavailable("simulated outage")
        if self.reply is not None:
            return self.reply
        return "\n".join(f"#{p['id']} {p['title']} suits you." for p in projects)


_counter = {"n": 0}


def make_designer(name=None):
    _counter["n"] += 1
    n = _counter["n"]
    designer = UserAccount.create(name or f"Designer {n}", f"chat-d{n}@example.com", "pass123", "InteriorDesigner")
    Company.create(designer.id, f"Company {n}", f"REG{n:05d}", "1 Test Road", "61234567",
                   f"studio{n}@example.com", "Test studio")
    return designer


def make_idp(budget, category="Kitchen", styles="Modern", designer=None, published=True, views=0,
             property_type="HDB", location="Tampines", title=None):
    designer = designer or make_designer()
    idp = IDP.create(designer.id, title or f"{category} {budget}", "test", category, budget, style_tags=styles,
                     property_type=property_type, location=location, published=published)
    if views:
        with get_connection() as conn:
            conn.execute("UPDATE idp SET views = ? WHERE id = ?", (views, idp.id))
    return IDP.find_by_id(idp.id)
