"""
utils.py

Contains mock tenant data and reusable mappings for type normalization and stakeholder routing,
as well as helper functions for tenant context lookup.

Used throughout the Domos Email Assistant project.
"""

# Mock tenant data simulating information from a tenant database
MOCK_TENANT_DATA = {
    "schaudhry216@gmail.com": {
        "name": "Shane Chaudhry",
        "unit": "2A",
        "balance_due": "$0",
        "lease_start": "2024-05-01",
        "lease_end": "2025-04-30",
        "recent_requests": ["AC repair in April", "Plumbing issue in March"]
    },
    "janedoe@example.com": {
        "name": "Jane Doe",
        "unit": "3B",
        "balance_due": "$150",
        "lease_start": "2023-10-01",
        "lease_end": "2024-09-30",
        "recent_requests": []
    },
    "david.smith@renters.net": {
        "name": "David Smith",
        "unit": "1C",
        "balance_due": "$75",
        "lease_start": "2024-01-15",
        "lease_end": "2024-12-31",
        "recent_requests": ["Broken heater in January"]
    },
    "maria.lopez@samplemail.com": {
        "name": "Maria Lopez",
        "unit": "4D",
        "balance_due": "$0",
        "lease_start": "2023-08-01",
        "lease_end": "2024-07-31",
        "recent_requests": ["Light fixture flickering", "Window jammed in February"]
    }
}

# Maps vague or inconsistent LLM output types to normalized internal workflow types
TYPE_NORMALIZATION_MAP = {
    "maintenance": "maintenance_request",
    "maintenance_request": "maintenance_request",
    "hvac": "maintenance_request",
    "plumbing": "maintenance_request",
    "leak": "maintenance_request",
    "payment": "payment_inquiry",
    "rent": "payment_inquiry",
    "invoice": "payment_inquiry",
    "lease": "lease_info_request",
    "contract": "lease_info_request",
    "lockout": "access_issue",
    "locked out": "access_issue",
    "access": "access_issue",
    "callback": "callback_request",
    "call me": "callback_request",
    "pest": "pest_issue",
    "infestation": "pest_issue",
    "maintenance + payment": "maintenance_and_payment_dispute"
}

# Maps action item types to stakeholder email addresses for CC routing
STAKEHOLDER_CC_MAP = {
    "maintenance_request": "maintenance@propertymanager.com",
    "pest_issue": "maintenance@propertymanager.com",
    "payment_inquiry": "accounting@propertymanager.com",
    "lease_info_request": "leasing@propertymanager.com",
    "access_issue": "security@propertymanager.com",
    "callback_request": "support@propertymanager.com",
    "maintenance_and_payment_dispute": "ops@propertymanager.com"
}

def get_tenant_context(email_address: str) -> dict:
    """
    Returns mocked tenant information for a given email address.
    If the email is not found, returns default values.

    Args:
        email_address (str): The tenant's email address

    Returns:
        dict: Tenant context data
    """
    return MOCK_TENANT_DATA.get(email_address, {
        "name": "Unknown",
        "unit": "Unknown",
        "balance_due": "Unknown",
        "lease_start": "Unknown",
        "lease_end": "Unknown",
        "recent_requests": []
    })
