app_name = "naqil"
app_title = "Naqil"
app_publisher = "Naqil Platform"
app_description = "Saudi Freight Marketplace and Fleet SaaS"
app_email = "admin@naqil.sa"
app_license = "MIT"

fixtures = [
    {
        "dt": "Role",
        "filters": [
            [
                "name",
                "in",
                [
                    "Naqil Administrator",
                    "Naqil Operations Manager",
                    "Naqil Verification Reviewer",
                    "Naqil Finance Officer",
                    "Naqil Support Agent",
                    "Naqil Customer",
                    "Naqil Carrier",
                    "Naqil Fleet Manager",
                ],
            ]
        ],
    },
    {"dt": "Workspace", "filters": [["name", "=", "Naqil"]]},
]

scheduler_events = {
    "hourly": [
        "naqil.tasks.run_due_auction_sweep",
        "naqil.tasks.refresh_backhaul_recommendations",
    ],
    "daily": [
        "naqil.tasks.send_expiry_reminders",
        "naqil.tasks.create_daily_operations_summary",
    ],
}

doc_events = {
    "Shipment Request": {
        "on_update": "naqil.events.shipments.on_shipment_update",
    },
    "Carrier Bid": {
        "after_insert": "naqil.events.auctions.on_bid_created",
    },
}

permission_query_conditions = {
    "Naqil Verification Case": "naqil.access.verification_case_query_condition",
    "Naqil Document Evidence": "naqil.access.document_evidence_query_condition",
    "Naqil Shipment": "naqil.access.shipment_query_condition",
    "Naqil Carrier Offer": "naqil.access.carrier_offer_query_condition",
    "Naqil Delivery Evidence": "naqil.access.delivery_evidence_query_condition",
    "Naqil Invoice": "naqil.access.invoice_query_condition",
    "Naqil Settlement": "naqil.access.settlement_query_condition",
}

has_permission = {
    "Naqil Organization": "naqil.access.organization_has_permission",
    "Naqil Membership": "naqil.access.membership_has_permission",
    "Naqil Verification Case": "naqil.access.verification_case_has_permission",
    "Naqil Document Evidence": "naqil.access.document_evidence_has_permission",
    "Naqil Shipment": "naqil.access.shipment_has_permission",
    "Naqil Carrier Offer": "naqil.access.carrier_offer_has_permission",
    "Naqil Delivery Evidence": "naqil.access.delivery_evidence_has_permission",
    "Naqil Invoice": "naqil.access.invoice_has_permission",
    "Naqil Settlement": "naqil.access.settlement_has_permission",
}

website_route_rules = [{"from_route": "/naqil", "to_route": "naqil"}]
