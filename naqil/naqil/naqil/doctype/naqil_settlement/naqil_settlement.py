import frappe
from frappe.model.document import Document
from frappe.utils import flt


class NaqilSettlement(Document):
    def validate(self):
        self.net_amount = flt(self.gross_amount) - flt(self.commission_amount)
        if self.net_amount < 0:
            frappe.throw("Settlement commission cannot exceed the gross amount.")
