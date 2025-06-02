"""
workflow.py

Handles extraction of structured action items from incoming email messages using:
- Mistral-7B via Together.ai for LLM-based classification
- Rule-based logic as a fallback when LLM fails or is unavailable
"""

import os
import json
import requests
from datetime import datetime
from utils import TYPE_NORMALIZATION_MAP, STAKEHOLDER_CC_MAP


TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")


def rule_based_action_item(email_body: str, subject: str = "", tenant_email: str = "", tenant_unit: str = "") -> dict:
    """
    Extracts action item metadata using keyword-based logic.

    Returns a dictionary including type, issue, location, and other metadata fields.
    """
    text = f"{subject} {email_body}".lower()

    action_item = {
        "type": None,
        "location": None,
        "issue": None,
        "status": "open",
        "tenant_email": tenant_email,
        "unit": tenant_unit,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "original_text": email_body.strip(),
        "priority": "normal"
    }

    for loc in ["kitchen", "bathroom", "living room", "bedroom", "garage", "hallway"]:
        if loc in text:
            action_item["location"] = loc
            break

    if any(word in text for word in ["urgent", "emergency", "asap"]):
        action_item["priority"] = "high"

    # Issue classification
    if "locked" in text or "lock" in text:
        action_item["type"] = "access_issue"
        action_item["issue"] = "lockout"
    elif any(kw in text for kw in ["money order", "not paying", "toilet"]):
        action_item["type"] = "maintenance_and_payment_dispute"
        action_item["issue"] = "payment withheld due to maintenance"
    elif ("rent" in text and "how much" in text) or "monthly rent" in text or "lease" in text:
        action_item["type"] = "lease_info_request"
        action_item["issue"] = "rent inquiry"
    elif any(kw in text for kw in ["call me", "call back", "available"]):
        action_item["type"] = "callback_request"
        action_item["issue"] = "tenant requested a phone call"
    elif any(kw in text for kw in ["leak", "pipe", "plumbing", "flood"]):
        action_item["type"] = "maintenance_request"
        action_item["issue"] = "plumbing leak"
    elif any(kw in text for kw in ["window", "glass", "crack"]):
        action_item["type"] = "maintenance_request"
        action_item["issue"] = "window damage"
    elif any(kw in text for kw in ["ac", "air conditioner", "heat", "hvac"]):
        action_item["type"] = "maintenance_request"
        action_item["issue"] = "hvac issue"
    elif any(kw in text for kw in ["mouse", "rat", "roach", "pest", "bug", "infestation"]):
        action_item["type"] = "pest_issue"
        action_item["issue"] = "pest report"
    elif any(kw in text for kw in ["rent", "payment", "balance", "paid"]):
        action_item["type"] = "payment_inquiry"
        action_item["issue"] = "rent confirmation"

    action_item["cc"] = STAKEHOLDER_CC_MAP.get(action_item["type"], "ops@propertymanager.com")
    return action_item


def extract_action_item(email_body: str, subject: str = "", tenant_email: str = "", tenant_unit: str = "") -> dict:
    """
    Uses Together.ai (Mistral-7B) to classify a tenant email and extract structured action item fields.
    Falls back to rule-based logic if LLM fails or returns invalid JSON.

    Returns:
        dict: action item object with normalized type and routed CC
    """
    prompt = (
        f"Classify the following email from a tenant and extract an action item in JSON format.\n\n"
        f"Email:\n\"\"\"{subject} {email_body}\"\"\"\n\n"
        f"Return only a JSON object with the following fields:\n"
        f"type, issue, location, priority"
    )

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.1",
        "messages": [
            {"role": "system", "content": "You are an assistant for property managers. Your job is to classify emails and extract action items."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 256,
        "temperature": 0.4
    }

    try:
        response = requests.post("https://api.together.xyz/v1/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        parsed = json.loads(content)

        raw_type = parsed.get("type", "").lower()
        normalized_type = "other"

        for keyword, mapped_type in TYPE_NORMALIZATION_MAP.items():
            if keyword in raw_type:
                normalized_type = mapped_type
                break

        return {
            "type": normalized_type,
            "location": parsed.get("location"),
            "issue": parsed.get("issue"),
            "status": "open",
            "tenant_email": tenant_email,
            "unit": tenant_unit,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "original_text": email_body.strip(),
            "priority": parsed.get("priority", "normal"),
            "cc": STAKEHOLDER_CC_MAP.get(normalized_type, "ops@propertymanager.com")
        }

    except Exception as e:
        print(f"⚠️ Together.ai LLM workflow classification failed: {e}")
        return rule_based_action_item(email_body, subject, tenant_email, tenant_unit)
