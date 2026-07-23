import os
from dotenv import load_dotenv
from zcatalyst_sdk import initialize_app, credentials, ICatalystOptions

# Load environment variables from .env
load_dotenv()

# ---------------------------------------------------------------------------
# Main Seeding Execution
# ---------------------------------------------------------------------------
def run():
    print("\n==================================================")
    print("      STARTING ZOHO CATALYST DATA SEEDING         ")
    print("==================================================\n")

    client_id = os.getenv("ZC_SDK_CLIENT_ID")
    client_secret = os.getenv("ZC_SDK_CLIENT_SECRET")
    refresh_token = os.getenv("ZC_SDK_REFRESH_TOKEN")
    project_id = os.getenv("CATALYST_PROJECT_ID", "51748000000013048")
    project_key = os.getenv("CATALYST_PROJECT_KEY", "60079342823")

    if not all([client_id, client_secret, refresh_token]):
        print("[CRITICAL ERROR] Missing OAuth credentials in .env file.")
        print("Ensure ZC_SDK_CLIENT_ID, ZC_SDK_CLIENT_SECRET, and ZC_SDK_REFRESH_TOKEN are set.")
        return

    try:
        # UserCredential handles token generation and automatic refreshes
        catalyst_credential = credentials.UserCredential({
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token
        })
        
        catalyst_options = ICatalystOptions(
            project_id=project_id,
            project_key=project_key,
            project_domain="https://api.catalyst.zoho.in",
            environment="Development"
        )

        app = initialize_app(
            credential=catalyst_credential,
            options=catalyst_options
        )
        print("[SUCCESS] SDK Initialized with UserCredential (Refresh Token).")
    except Exception as e:
        print(f"[CRITICAL ERROR] SDK Initialization failed: {e}")
        return

    try:
        datastore = app.datastore()
        print("[SUCCESS] Catalyst Data Store Service connected!\n")
    except Exception as exc:
        print(f"[CRITICAL ERROR] Could not get Data Store service: {exc}")
        return

    # 1. Generate & Insert CaseMaster records
    cases = generate_mock_cases(20)
    inserted_firs = []
    case_table = datastore.table("CaseMaster")
    
    print(f"Attempting to seed {len(cases)} CaseMaster records...")
    for case in cases:
        try:
            case_table.insert_row(case)
            inserted_firs.append(case['FIRNumber'])
            print(f"  [+] Inserted Case: {case['FIRNumber']}")
        except Exception as err:
            print(f"  [-] Failed to insert Case {case.get('FIRNumber')}: {err}")

    # 2. Generate & Insert Accused records
    if inserted_firs:
        accused_records = generate_mock_accused(inserted_firs, 30)
        accused_table = datastore.table("Accused")
        print(f"\nAttempting to seed {len(accused_records)} Accused records...")
        for accused in accused_records:
            try:
                accused_table.insert_row(accused)
                print(f"  [+] Inserted Accused: {accused['Name']} ({accused['FIRNumber']})")
            except Exception as err:
                print(f"  [-] Failed to insert Accused {accused['Name']}: {err}")
    else:
        print("\n[!] Skipping Accused seeding as no CaseMaster records were inserted successfully.")

    print("\n==================================================")
    print("              SEEDING SCRIPT COMPLETED             ")
    print("==================================================\n")


if __name__ == "__main__":
    run()