import frappe
from frappe.utils import now_datetime

from naqil.services.auction import close_due_auction


def run_due_auction_sweep():
    due_shipments = frappe.get_all(
        "Naqil Shipment",
        filters={"status": "Open for Bidding", "auction_end": ["<=", now_datetime()]},
        pluck="name",
    )
    closed_count = 0
    for shipment_name in due_shipments:
        if close_due_auction(shipment_name):
            closed_count += 1
    frappe.logger("naqil").info("Naqil auction sweep closed %s auctions", closed_count)


def refresh_backhaul_recommendations():
    policy = frappe.get_all(
        "Naqil Backhaul Policy",
        filters={"status": "Active"},
        fields=["name", "max_matches_per_trip"],
        limit=1,
    )
    if not policy:
        frappe.logger("naqil").warning("No active Naqil backhaul policy is configured")
        return

    for capacity in frappe.get_all(
        "Naqil Backhaul Capacity",
        filters={"status": "Available", "marketplace_opt_in": 1},
        fields=["name", "origin_city", "destination_city", "capacity_weight_kg", "available_from", "available_until"],
    ):
        candidates = frappe.get_all(
            "Naqil Shipment",
            filters={
                "status": "Open for Bidding",
                "pickup_city": capacity.origin_city,
                "delivery_city": capacity.destination_city,
                "cargo_weight_kg": ["<=", capacity.capacity_weight_kg],
            },
            fields=["name", "shipment_title"],
            order_by="auction_end asc",
            limit_page_length=policy[0].max_matches_per_trip,
        )
        for shipment in candidates:
            if frappe.db.exists(
                "Naqil Backhaul Recommendation",
                {"capacity": capacity.name, "shipment": shipment.name, "status": "Suggested"},
            ):
                continue
            frappe.get_doc(
                {
                    "doctype": "Naqil Backhaul Recommendation",
                    "capacity": capacity.name,
                    "shipment": shipment.name,
                    "policy": policy[0].name,
                    "match_score": 100,
                    "explanation": "Exact route, available capacity, and active marketplace opt-in matched under the active backhaul policy.",
                }
            ).insert()


def send_expiry_reminders():
    expired_documents = frappe.get_all(
        "Naqil Document Evidence",
        filters={"expiry_date": ["<", now_datetime().date()], "status": ["!=", "Expired"]},
        pluck="name",
    )
    for name in expired_documents:
        frappe.db.set_value("Naqil Document Evidence", name, "status", "Expired", update_modified=False)


def create_daily_operations_summary():
    stats = {
        "open_auctions": frappe.db.count("Naqil Shipment", {"status": "Open for Bidding"}),
        "selection_due": frappe.db.count("Naqil Shipment", {"status": "Selection Due"}),
        "pending_verification": frappe.db.count("Naqil Verification Case", {"status": ["in", ["Open", "Under Review"]]}),
    }
    frappe.logger("naqil").info("Naqil daily operations summary: %s", stats)
