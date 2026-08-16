from frappe.model.document import Document
from frappe.utils import flt


class NaqilInvoice(Document):
    def validate(self):
        self.commission_amount = flt(self.subtotal_amount) * flt(self.commission_rate) / 100
        self.total_amount = flt(self.subtotal_amount) + flt(self.commission_amount)
