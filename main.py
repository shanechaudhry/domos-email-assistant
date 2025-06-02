"""
main.py

Entry point for the Domos Email Assistant.
Connects to Gmail, fetches unread emails, classifies and responds to each one,
and logs action items to a local JSON file.
"""

import json
import os
import re
from email_client import connect_to_gmail, fetch_unread_emails, send_reply
from responder import generate_reply
from workflow import extract_action_item
from utils import get_tenant_context


if __name__ == "__main__":
    # Connect to Gmail inbox
    mail = connect_to_gmail()

    # Fetch all unread emails
    emails = fetch_unread_emails(mail)

    for email in emails:
        print("\n--- ORIGINAL ---")
        print(email["body"])

        # Extract sender email from raw address format
        match = re.search(r'<(.+?)>', email["from"])
        to_address = match.group(1) if match else email["from"]

        # Load tenant context (mocked)
        tenant_context = get_tenant_context(to_address)
        print("\n--- TENANT INFO ---")
        print(tenant_context)

        # Generate a reply (LLM or rule-based)
        reply = generate_reply(email["body"], tenant_context)
        print("\n--- AI REPLY ---")
        print(reply)

        # Generate an action item from email
        action_item = extract_action_item(
            email["body"],
            email["subject"],
            tenant_email=to_address,
            tenant_unit=tenant_context.get("unit", "unknown")
        )

        if action_item["type"]:
            output_path = "output/action_items.json"

            # Load existing items (if valid), else start fresh
            if os.path.exists(output_path):
                try:
                    with open(output_path, "r") as f:
                        action_items = json.load(f)
                        if not isinstance(action_items, list):
                            print("⚠️  Existing file is not a list — resetting.")
                            action_items = []
                except (json.JSONDecodeError, IOError):
                    print("⚠️  Failed to load existing JSON — resetting.")
                    action_items = []
            else:
                action_items = []

            # Append and write new action item
            action_items.append(action_item)
            with open(output_path, "w") as f:
                json.dump(action_items, f, indent=2)

            print(f"\n--- ACTION ITEM APPENDED TO {output_path} ---")
            print(json.dumps(action_item, indent=2))
        else:
            print("\nNo workflow action detected.")

        # Send the reply via SMTP
        send_reply(to_address, email["subject"], reply, cc=action_item.get("cc", "ops@propertymanager.com"))
        print(f"\n--- REPLY SENT TO {to_address} (CC: {action_item.get('cc')}) ---")
