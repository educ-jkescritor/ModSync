import requests
from datetime import datetime

def check_tech(product, version):
    print(f"\n--- Checking {product.upper()} (Version {version}) ---")
    api_url = f"https://endoflife.date/api/{product}/{version}.json"
    
    print(f"1. Sending GET request to: {api_url}")
    try:
        response = requests.get(api_url, timeout=3)
        print(f"2. Server responded with Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            eol_date = data.get("eol")
            print(f"3. Raw JSON received: {data}")
            
            if eol_date:
                today = datetime.now().strftime("%Y-%m-%d")
                is_past = eol_date < today
                if is_past:
                    print(f"4. VERDICT: DEAD (It reached End of Life on {eol_date})")
                else:
                    print(f"4. VERDICT: ACTIVE (It is supported until {eol_date})")
            else:
                print("4. VERDICT: ACTIVE (No End of Life date announced yet)")
        else:
            print("3. VERDICT: NOT FOUND (The API does not have this specific version)")
            
    except Exception as e:
        print(f"Error: {e}")

# Test a dead technology (PHP 5.6)
check_tech("php", "5.6")

# Test an active technology (Python 3.12)
check_tech("python", "3.12")
