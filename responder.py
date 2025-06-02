"""
responder.py

Handles reply generation for incoming tenant emails using:
- Together.ai (Mistral-7B) for LLM-generated responses
- Rule-based logic as fallback
"""

import os
import requests

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")


def generate_rule_based_reply(email_body: str, tenant_context: dict) -> str:
    """
    Generates a response based on predefined rules and keyword matching.

    Args:
        email_body (str): The tenant's email message
        tenant_context (dict): Info about the tenant (name, unit, lease, etc.)

    Returns:
        str: A formatted plain-text email reply
    """
    message = email_body.lower()
    name = tenant_context["name"]
    unit = tenant_context["unit"]

    if "locked" in message or "lock" in message:
        return (
            f"Hi {name},\n\n"
            f"We understand you're locked out of Unit {unit}. If this is urgent, please contact building security or call management directly. "
            f"We can also coordinate access during regular hours.\n\n"
            f"- Property Management"
        )
    elif "money order" in message or "not paying" in message or "toilet" in message:
        return (
            f"Hi {name},\n\n"
            f"Thanks for letting us know. We'll log a maintenance ticket for the issue in Unit {unit}. "
            f"Meanwhile, please don’t hesitate to reach out about payment concerns — we’re here to help.\n\n"
            f"- Property Management"
        )
    elif ("rent" in message and "how much" in message) or "monthly rent" in message or "lease" in message:
        return (
            f"Hi {name},\n\n"
            f"Your lease began on {tenant_context['lease_start']} and runs through {tenant_context['lease_end']}. "
            f"We can confirm your rent amount or resend your lease if needed — just let us know!\n\n"
            f"- Property Management"
        )
    elif "call me" in message or "call back" in message or "available" in message or "tomorrow" in message:
        return (
            f"Hi {name},\n\n"
            f"Thanks for your message. We’ll follow up with a call around your availability tomorrow.\n\n"
            f"- Property Management"
        )
    elif any(kw in message for kw in ["leak", "pipe", "plumbing", "flood"]):
        return (
            f"Hi {name},\n\n"
            f"Thanks for reporting the plumbing issue in Unit {unit}. We'll dispatch maintenance shortly.\n\n"
            f"- Property Management"
        )
    elif any(kw in message for kw in ["window", "glass", "crack"]):
        return (
            f"Hi {name},\n\n"
            f"We’ll send someone to look into the window issue in Unit {unit} as soon as possible.\n\n"
            f"- Property Management"
        )
    elif any(kw in message for kw in ["ac", "air conditioner", "heat", "hvac"]):
        return (
            f"Hi {name},\n\n"
            f"We’ll have the HVAC team review the issue in Unit {unit}. We’ll reach out to schedule access.\n\n"
            f"- Property Management"
        )
    elif any(kw in message for kw in ["rent", "payment", "paid", "balance"]):
        return (
            f"Hi {name},\n\n"
            f"We'll confirm your payment status and follow up with any updates on your balance.\n\n"
            f"- Property Management"
        )
    elif any(kw in message for kw in ["mouse", "rat", "roach", "pest", "bug", "infestation"]):
        return (
            f"Hi {name},\n\n"
            f"We’re arranging pest control for Unit {unit}. We'll notify you when the visit is scheduled.\n\n"
            f"- Property Management"
        )

    return None


def generate_reply(email_body: str, tenant_context: dict) -> str:
    """
    Generates a reply using Together.ai (LLM) or falls back to rule-based logic.

    Args:
        email_body (str): Raw tenant email content
        tenant_context (dict): Tenant metadata

    Returns:
        str: AI-generated or fallback plain-text reply
    """
    name = tenant_context["name"]
    unit = tenant_context["unit"]

    prompt = (
        f"You are a helpful and professional assistant who replies on behalf of Property Management. "
        f"Always sign off with: 'Property Management'.\n\n"
        f"Tenant Info:\n"
        f"- Name: {name}\n"
        f"- Unit: {unit}\n"
        f"- Lease: {tenant_context['lease_start']} to {tenant_context['lease_end']}\n"
        f"- Balance Due: {tenant_context['balance_due']}\n"
        f"- Recent Requests: {', '.join(tenant_context['recent_requests']) or 'None'}\n\n"
        f"Tenant Message:\n{email_body.strip()}\n\n"
        f"Reply (signed as Property Management):"
    )

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.1",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant for property management."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 256,
        "temperature": 0.7
    }

    try:
        response = requests.post("https://api.together.xyz/v1/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"⚠️ Together.ai API failed, falling back to rule-based reply: {e}")
        rule_based = generate_rule_based_reply(email_body, tenant_context)
        return rule_based or "(No suitable rule-based reply available.)"
