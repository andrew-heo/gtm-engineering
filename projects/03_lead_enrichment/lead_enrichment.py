import os
import re
from datetime import datetime, timezone

import pandas as pd
import requests
from simple_salesforce import Salesforce

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

SFDC_CONFIG = {
    "username": "andrew.heo@company.com",
    "password": "fake_password_123",
    "security_token": "fake_security_token_abc",
    "domain": "login",   # use "test" for sandbox
}

SLACK_CONFIG = {
    "bot_token": "xoxb-fake-slack-token",
    "unowned_demo_request_channel": "#unowneddemorequest",
}

CLAY_CONFIG = {
    "api_key": "clay_fake_api_key_123",
    "base_url": "https://api.clay.com/v1",
}

UNIFY_CONFIG = {
    "api_key": "unify_fake_api_key_123",
    "base_url": "https://api.unifygtm.com/v1",
}

PERSONAL_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "icloud.com",
}

REQUEST_SOURCE = "Online Demo Request"
LAST_INTERESTING_MOMENT_FIELD = "Last_Interesting_Moment__c"

demo_request = {
    "first_name": "Andrew",
    "last_name": "Heo",
    "company_email": "andrew@acme.com",
    "company_name": "Acme",
    "job_title": "Head of Operations",
    "country": "US",
    "request_timestamp": datetime.now(timezone.utc).isoformat(),
    "request_source": "online_demo_request",
}
# -------------------------------------------------------------------
# Basic helpers
# -------------------------------------------------------------------

def extract_email_domain(company_email):
    return company_email.split("@")[-1].lower().strip()


def is_company_email(company_email):
    email_domain = extract_email_domain(company_email)
    return email_domain not in PERSONAL_EMAIL_DOMAINS


def format_last_interesting_moment_value(request_timestamp):
    request_date = datetime.fromisoformat(
        request_timestamp.replace("Z", "+00:00")
    ).date()
    return f"Online demo request ({request_date})"

# -------------------------------------------------------------------
# Salesforce
# -------------------------------------------------------------------

def connect_to_salesforce():
    sf = Salesforce(
        username=SFDC_CONFIG["username"],
        password=SFDC_CONFIG["password"],
        security_token=SFDC_CONFIG["security_token"],
        domain=SFDC_CONFIG["domain"],
    )
    return sf
# -------------------------------------------------------------------
# Clay enrichment
# -------------------------------------------------------------------

def enrich_person_and_company_with_clay(company_email):
    payload = {
        "email": company_email,
    }

    response = requests.post(
        f"{CLAY_CONFIG['base_url']}/enrich",
        headers={
            "Authorization": f"Bearer {CLAY_CONFIG['api_key']}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    return response.json()

# -------------------------------------------------------------------
# Lead lookup / creation
# -------------------------------------------------------------------

def find_existing_lead_by_email(sf, company_email):
    soql = f"""
        SELECT Id, Email, Company, OwnerId
        FROM Lead
        WHERE Email = '{company_email}'
        LIMIT 1
    """
    result = sf.query(soql)
    records = result.get("records", [])
    return records[0] if records else None


def create_lead_from_demo_request(sf, demo_request, clay_enrichment):
    payload = {
        "FirstName": demo_request["first_name"],
        "LastName": demo_request["last_name"],
        "Email": demo_request["company_email"],
        "Company": clay_enrichment.get("company_name", demo_request["company_name"]),
        "Title": clay_enrichment.get("job_title", demo_request["job_title"]),
        "LeadSource": REQUEST_SOURCE,
    }

    return sf.Lead.create(payload)

# -------------------------------------------------------------------
# Account matching
# -------------------------------------------------------------------

def find_account_by_email_domain(sf, email_domain):
    soql = f"""
        SELECT Id, Name, OwnerId, Domain__c
        FROM Account
        WHERE Domain__c = '{email_domain}'
        LIMIT 1
    """
    result = sf.query(soql)
    records = result.get("records", [])
    return records[0] if records else None

# -------------------------------------------------------------------
# Account update
# -------------------------------------------------------------------

def update_last_interesting_moment(sf, account_id, request_timestamp):
    payload = {
        LAST_INTERESTING_MOMENT_FIELD: format_last_interesting_moment_value(request_timestamp)
    }
    return sf.Account.update(account_id, payload)
# -------------------------------------------------------------------
# Slack
# -------------------------------------------------------------------

def send_slack_message(slack_destination, message_text):
    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={
            "Authorization": f"Bearer {SLACK_CONFIG['bot_token']}",
            "Content-Type": "application/json; charset=utf-8",
        },
        json={
            "channel": slack_destination,
            "text": message_text,
        },
        timeout=30,
    )
    return response.json()
  # -------------------------------------------------------------------
# Salesforce owner -> Slack mapping
# -------------------------------------------------------------------

SFDC_OWNER_ID_TO_SLACK_DESTINATION = {
    "0058A000001AAA1": "U11111111",   # AE_1
    "0058A000001AAA2": "U22222222",   # AE_2
    "0058A000001AAA3": "U33333333",   # AE_3
    "0058A000001AAA4": "U44444444",   # AE_4
}

def map_salesforce_owner_id_to_slack_destination(owner_id):
    return SFDC_OWNER_ID_TO_SLACK_DESTINATION.get(
        owner_id,
        SLACK_CONFIG["unowned_demo_request_channel"]
    )
  def build_demo_request_slack_message(
    demo_request,
    clay_enrichment,
    matched_account,
    lead_record,
):
    enriched_full_name = clay_enrichment.get(
        "full_name",
        f"{demo_request['first_name']} {demo_request['last_name']}"
    )

    enriched_job_title = clay_enrichment.get(
        "job_title",
        demo_request["job_title"]
    )

    enriched_company_name = clay_enrichment.get(
        "company_name",
        demo_request["company_name"]
    )

    enriched_company_size = clay_enrichment.get("company_size")
    enriched_industry = clay_enrichment.get("industry")

    matched_account_name = matched_account.get("Name") if matched_account else "None"
    lead_id = lead_record.get("Id") if lead_record else "None"

    message_lines = [
        "New online demo request",
        f"Name: {enriched_full_name}",
        f"Email: {demo_request['company_email']}",
        f"Title: {enriched_job_title}",
        f"Company: {enriched_company_name}",
        f"Matched account: {matched_account_name}",
        f"Lead ID: {lead_id}",
    ]

    if enriched_company_size:
        message_lines.append(f"Company size: {enriched_company_size}")

    if enriched_industry:
        message_lines.append(f"Industry: {enriched_industry}")

    return "\n".join(message_lines)

# -------------------------------------------------------------------
# Unify
# -------------------------------------------------------------------

def send_demo_request_signal_to_unify(demo_request, matched_account, lead_record):
    payload = {
        "email": demo_request["company_email"],
        "company_name": demo_request["company_name"],
        "request_source": demo_request["request_source"],
        "request_timestamp": demo_request["request_timestamp"],
        "salesforce_lead_id": lead_record.get("Id") if lead_record else None,
        "salesforce_account_id": matched_account.get("Id") if matched_account else None,
    }

    response = requests.post(
        f"{UNIFY_CONFIG['base_url']}/signals/demo-request",
        headers={
            "Authorization": f"Bearer {UNIFY_CONFIG['api_key']}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    return response.json()

# -------------------------------------------------------------------
# Main workflow
# -------------------------------------------------------------------

def main():
    company_email = demo_request["company_email"]

    if not is_company_email(company_email):
        raise ValueError("Demo request must use a company email.")

    email_domain = extract_email_domain(company_email)

    sf = connect_to_salesforce()

    clay_enrichment = enrich_person_and_company_with_clay(company_email)

    existing_lead = find_existing_lead_by_email(sf, company_email)

    if existing_lead:
        lead_record = existing_lead
    else:
        create_result = create_lead_from_demo_request(sf, demo_request, clay_enrichment)
        lead_record = {"Id": create_result.get("id")}

    matched_account = find_account_by_email_domain(sf, email_domain)

    if matched_account:
        update_last_interesting_moment(
            sf=sf,
            account_id=matched_account["Id"],
            request_timestamp=demo_request["request_timestamp"],
        )

        owner_id = matched_account.get("OwnerId")

        if owner_id:
            slack_destination = map_salesforce_owner_id_to_slack_destination(owner_id)
        else:
            slack_destination = SLACK_CONFIG["unowned_demo_request_channel"]
    else:
        slack_destination = SLACK_CONFIG["unowned_demo_request_channel"]

    slack_message = build_demo_request_slack_message(
        demo_request=demo_request,
        clay_enrichment=clay_enrichment,
        matched_account=matched_account,
        lead_record=lead_record,
    )
    send_slack_message(slack_destination, slack_message)

    send_demo_request_signal_to_unify(
        demo_request=demo_request,
        matched_account=matched_account,
        lead_record=lead_record,
    )


if __name__ == "__main__":
    main()



