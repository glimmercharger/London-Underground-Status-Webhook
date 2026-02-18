import requests
import time

# --- CONFIGURATION ---
WEBHOOK_URL = "YOUR_WEBHOOK_URL_HERE"
API_KEY = "YOUR_TFL_PRIMARY_KEY_HERE"

# PASTE YOUR ROLE ID HERE (e.g., "123456789012345678")
# Leave it as "" if you don't want any pings.
DISCORD_ROLE_ID = ""

TFL_API_URL = f"https://api.tfl.gov.uk/line/mode/tube/status?app_key={API_KEY}"

last_report_content = ""

def get_tube_status():
    try:
        response = requests.get(TFL_API_URL)
        response.raise_for_status()
        data = response.json()
        
        status_updates = []
        for line in data:
            name = line['name']
            status_info = line['lineStatuses'][0]
            status_desc = status_info['statusSeverityDescription']
            
            if status_desc != "Good Service":
                reason = status_info.get('reason', "No details provided.")
                status_updates.append(f"⚠️ **{name} Line**: {status_desc}\n*{reason}*")
        
        if not status_updates:
            return "✅ **All Tube lines: Good Service**"
        
        return "\n\n".join(status_updates)

    except Exception as e:
        return f"❌ API Error: {e}"

def send_to_webhook(message):
    # Logic: If a Role ID exists, prepend the mention to the message
    if DISCORD_ROLE_ID:
        full_message = f"<@&{DISCORD_ROLE_ID}>\n{message}"
    else:
        full_message = message

    payload = {"content": full_message}
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        if response.status_code in [200, 204]:
            print(f"[{time.strftime('%H:%M:%S')}] Webhook sent successfully.")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] Webhook failed: {response.status_code}")
    except Exception as e:
        print(f"Error sending to Webhook: {e}")

if __name__ == "__main__":
    print("Tube Monitor Active. Checking every 5 minutes...")
    
    while True:
        current_report = get_tube_status()
        
        if current_report != last_report_content:
            send_to_webhook(current_report)
            last_report_content = current_report
        else:
            print(f"[{time.strftime('%H:%M:%S')}] Checked: No changes found.")

        time.sleep(300)
