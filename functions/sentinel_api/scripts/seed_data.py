import os
import sys
import logging
import random
import requests
from datetime import date, timedelta
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from dotenv import load_dotenv
load_dotenv()

os.environ["CATALYST_ENV"] = "Development"
os.environ.pop("CATALYST_LOCAL", None)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

TABLE_COLUMNS_CACHE = {}

# ---------------------------------------------------------------------------
# Helper 1: Fetch OAuth Access Token
# ---------------------------------------------------------------------------
def get_fresh_access_token(client_id: str, client_secret: str, refresh_token: str, accounts_url: str = "https://accounts.zoho.in") -> str:
    """Exchanges refresh_token for a live short-lived access_token directly from Zoho Accounts."""
    token_url = f"{accounts_url}/oauth/v2/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    response = requests.post(token_url, data=payload)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch OAuth access token: {response.status_code} - {response.text}")
    
    data = response.json()
    if "access_token" not in data:
        raise KeyError(f"OAuth response missing 'access_token': {data}")
    
    return data["access_token"]


# ---------------------------------------------------------------------------
# Helper 2: Catalyst Schema Introspection
# ---------------------------------------------------------------------------
def get_table_columns(project_domain: str, project_id: str, table_name: str, access_token: str) -> list:
    """Fetches custom user column names defined in the Catalyst Data Store schema."""
    if table_name in TABLE_COLUMNS_CACHE:
        return TABLE_COLUMNS_CACHE[table_name]

    url = f"{project_domain}/baas/v1/project/{project_id}/table/{table_name}/column"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200 and resp.json().get("status") == "success":
            cols = [c["column_name"] for c in resp.json().get("data", [])]
            TABLE_COLUMNS_CACHE[table_name] = cols
            return cols
    except Exception as e:
        logger.warning(f"Could not introspect columns for {table_name}: {e}")
    
    return []


# ---------------------------------------------------------------------------
# Helper 3: Insert Row into Catalyst Data Store
# ---------------------------------------------------------------------------
def insert_table_row(project_domain: str, project_id: str, table_name: str, access_token: str, row_data: dict) -> dict:
    """Calls Catalyst REST API to insert a row."""
    url = f"{project_domain}/baas/v1/project/{project_id}/table/{table_name}/row"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=[row_data], headers=headers)
    
    if response.status_code not in (200, 201):
        raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
    
    res_json = response.json()
    if res_json.get("status") != "success":
        raise RuntimeError(f"API Error: {res_json}")
        
    return res_json


# ---------------------------------------------------------------------------
# Expanded Mock Data Generators
# ---------------------------------------------------------------------------
CRIME_GROUPS = ["Cyber Crime", "Financial Fraud", "Property Offense", "Body Offense", "White Collar Crime"]
CRIME_HEADS = [
    "Phishing", "Identity Theft", "Ransomware Attack", "Online Banking Fraud", 
    "Cheating & Forgery", "UPI / ATM Swindling", "Crypto Scam", "Data Breach"
]
UNITS = [
    "UNIT-101 (Bengaluru Urban)", "UNIT-102 (Mysuru City)", "UNIT-103 (Mangaluru City)",
    "UNIT-104 (Hubballi-Dharwad)", "UNIT-105 (Belagavi)", "UNIT-106 (Cyber Crime HQ)"
]
ACT_SECTIONS = [
    "IT Act Sec 66D / IPC 420", "IT Act Sec 66C", "IT Act Sec 43 / IPC 379", 
    "IPC 406 / IT Act Sec 66", "IPC 419 / IPC 420", "IT Act Sec 67A"
]
MODUS_OPERANDI = [
    "Spoofed bank URL sent via SMS to capture banking credentials",
    "Posed as customer care agent requesting AnyDesk remote application installation",
    "Unauthorized SIM swap executed followed by real-time OTP interception",
    "Fake e-commerce website created offering fake festive discounts",
    "Posed as army officer on OLX demanding advance token payment",
    "Extortion via fake loan app by accessing contact list and photo gallery",
    "Investment scam promising 200% returns via Telegram investment group",
    "Job offer scam requesting processing fees for fake international airline job"
]

FIRST_NAMES = [
    "Rahul", "Amit", "Priya", "Sanjay", "Neha", "Vikas", "Ananya", "Rohan", 
    "Kavya", "Deepak", "Aditya", "Meera", "Kiran", "Siddharth", "Pooja", "Arjun"
]
LAST_NAMES = [
    "Sharma", "Verma", "Patil", "Kulkarni", "Deshmukh", "Joshi", "Mehta", 
    "Gowda", "Rao", "Nair", "Hegde", "Shetty", "Kashyap", "Reddy"
]

def generate_mock_cases(count=50, start_id=1021):
    cases = []
    for i in range(count):
        curr_num = start_id + i
        case_id = f"CASE-2026-{curr_num}"
        fir_no = f"FIR-2026-{curr_num}"
        
        # Karnataka GPS Bounding Box
        lat = round(12.9716 + random.uniform(-0.3, 0.3), 6)
        lng = round(77.5946 + random.uniform(-0.3, 0.3), 6)
        
        cases.append({
            "CaseID": case_id,
            "UnitID": random.choice(UNITS),
            "FIRNumber": fir_no,
            "CrimeGroup": random.choice(CRIME_GROUPS),
            "CrimeHead": random.choice(CRIME_HEADS),
            "Latitude": str(lat),
            "Longitude": str(lng),
            "OffenseDate": f"{(date.today() - timedelta(days=random.randint(1, 150))).strftime('%Y-%m-%d')} {random.randint(8,22):02d}:{random.randint(0,59):02d}:00",
            "ActSection": random.choice(ACT_SECTIONS),
            "ModusOperandi": random.choice(MODUS_OPERANDI)
        })
    return cases

def generate_mock_accused(case_ids, count=100, start_id=2031):
    accused_list = []
    for i in range(count):
        accused_list.append({
            "AccusedID": f"ACC-2026-{start_id + i}",
            "CaseID": random.choice(case_ids),
            "Name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "Age": random.randint(19, 62),
            "Gender": random.choice(["Male", "Female"]),
            "ArrestStatus": random.choice(["Arrested", "Absconding", "Bail Granted", "Under Custody", "Notice Issued"]),
            "MODetails": random.choice(MODUS_OPERANDI)
        })
    return accused_list


# ---------------------------------------------------------------------------
# Main Seeding Pipeline
# ---------------------------------------------------------------------------
def run():
    print("\n==================================================")
    print("    STARTING EXPANDED CATALYST DATA SEEDING       ")
    print("==================================================\n")

    client_id = os.getenv("ZC_SDK_CLIENT_ID")
    client_secret = os.getenv("ZC_SDK_CLIENT_SECRET")
    refresh_token = os.getenv("ZC_SDK_REFRESH_TOKEN")
    project_id = os.getenv("CATALYST_PROJECT_ID", "51748000000013048")
    project_domain = os.getenv("CATALYST_PROJECT_DOMAIN", "https://api.catalyst.zoho.in")
    
    # Configure Record Counts (Defaults to 50 Cases, 100 Accused)
    CASE_COUNT = int(os.getenv("SEED_CASE_COUNT", 50))
    ACCUSED_COUNT = int(os.getenv("SEED_ACCUSED_COUNT", 100))
    START_CASE_NUM = int(os.getenv("SEED_START_CASE_ID", 1021))
    START_ACCUSED_NUM = int(os.getenv("SEED_START_ACCUSED_ID", 2031))

    accounts_domain = "https://accounts.zoho.com" if ".com" in project_domain else "https://accounts.zoho.in"

    if not all([client_id, client_secret, refresh_token]):
        print("[CRITICAL ERROR] Missing OAuth credentials in environment.")
        return

    # 1. Fetch live Access Token
    try:
        print("[+] Requesting fresh access token from Zoho Accounts...")
        access_token = get_fresh_access_token(client_id, client_secret, refresh_token, accounts_domain)
        print("[SUCCESS] Access token obtained successfully.\n")
    except Exception as e:
        print(f"[CRITICAL ERROR] Could not retrieve access token: {e}")
        return

    # 2. Verify Schema
    case_cols = get_table_columns(project_domain, project_id, "CaseMaster", access_token)
    accused_cols = get_table_columns(project_domain, project_id, "Accused", access_token)
    print(f"[INFO] Target Tables: CaseMaster ({len(case_cols)} cols), Accused ({len(accused_cols)} cols)\n")

    # 3. Seed CaseMaster
    cases = generate_mock_cases(count=CASE_COUNT, start_id=START_CASE_NUM)
    inserted_case_ids = []
    
    print(f"Attempting to seed {len(cases)} CaseMaster records...")
    for case in cases:
        try:
            insert_table_row(project_domain, project_id, "CaseMaster", access_token, case)
            inserted_case_ids.append(case["CaseID"])
            print(f"  [+] Inserted Case: {case['CaseID']} ({case['FIRNumber']})")
        except Exception as err:
            print(f"  [-] Failed to insert Case {case['CaseID']}: {err}")

    # 4. Seed Accused
    if inserted_case_ids:
        accused_records = generate_mock_accused(inserted_case_ids, count=ACCUSED_COUNT, start_id=START_ACCUSED_NUM)
        print(f"\nAttempting to seed {len(accused_records)} Accused records...")
        for accused in accused_records:
            try:
                insert_table_row(project_domain, project_id, "Accused", access_token, accused)
                print(f"  [+] Inserted Accused: {accused['Name']} -> {accused['CaseID']}")
            except Exception as err:
                print(f"  [-] Failed to insert Accused {accused['Name']}: {err}")
    else:
        print("\n[!] Skipping Accused seeding as no CaseMaster records were inserted successfully.")

    print("\n==================================================")
    print("            ADDITIONAL SEEDING COMPLETED           ")
    print("==================================================")


if __name__ == "__main__":
    run()