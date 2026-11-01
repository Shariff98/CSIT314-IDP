"""Control: NotifyMilestoneController (US-48 Notify on view or shortlist milestone)."""
from entity.notification import Notification

VIEW_MILESTONES = (10, 50, 100, 250, 500, 1000)
SHORTLIST_MILESTONES = (5, 10, 25, 50, 100)


class NotifyMilestoneController:
    def check(self, idp):
        """Called after a view or a save. Creates each milestone notification once. Returns the new ones."""
        created = []
        reached = [(m, "views") for m in VIEW_MILESTONES if idp.views >= m]
        reached += [(m, "shortlists") for m in SHORTLIST_MILESTONES if idp.shortlist_count() >= m]
        for milestone, kind in reached:
            message = f"'{idp.title}' reached {milestone} {kind}"
            if not Notification.exists(idp.id, message):
                created.append(Notification.create(idp.designer_id, idp.id, message))
        return created

    def list_notifications(self, designer_id):
        return Notification.list_for_designer(designer_id)

    def unread_count(self, designer_id):
        return len(Notification.list_for_designer(designer_id, unread_only=True))

    def mark_all_read(self, designer_id):
        Notification.mark_all_read(designer_id)
