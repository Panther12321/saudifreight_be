from frappe.model.document import Document
from frappe.utils import now_datetime


class NaqilBackhaulRecommendation(Document):
    def before_insert(self):
        self.created_on = now_datetime()
