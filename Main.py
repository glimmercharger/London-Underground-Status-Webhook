import requests
import time

# --- CONFIGURATION ---
WEBHOOK_URL = "Webhook URL"
API_KEY = "Your Primary TFL API"
DISCORD_ROLE_ID = "Your Discord Role ID" 

# Added 'dlr' to the modes in the URL
TFL_API_URL = f"https://api.tfl.gov.uk/line/mode/tube,dlr/status?app_key={API_KEY}"

line_memory = {}
last_heartbeat = time.time()
HEARTBEAT_INTERVAL = 10800 # 3 Hours

def get_tube_data():
    try:
        response = requests.get(TFL_API_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] API Error: {e}")
        return None

def send_to_discord(message, should_ping=False):
    content = f"<@&{DISCORD_ROLE_ID}>\n{message}" if (should_ping and DISCORD_ROLE_ID) else message
    try:
        requests.post(WEBHOOK_URL, json={"content": content})
    except Exception as e:
        print(f"Error sending to Webhook: {e}")

if __name__ == "__main__":
    print("Tube & DLR Monitor: Smart Summary Mode Active...")

    while True:
        data = get_tube_data()
        current_time = time.time()
        
        if data:
            disrupted_messages = []
            good_service_names = []
            alert_priority = False
            state_changed = False

            for line in data:
                name = line['name']
                status_obj = line['lineStatuses'][0]
                status_desc = status_obj['statusSeverityDescription']
                severity = status_obj['statusSeverity']
                reason = status_obj.get('reason', "")

                # Detect if the status has changed for this specific line
                if name not in line_memory or line_memory[name] != status_desc:
                    state_changed = True
                    line_memory[name] = status_desc

                # Categorize the line status
                if severity < 10:
                    disrupted_messages.append(f"🚇 **{name}**: {status_desc}\n*{reason}*")
                    if severity <= 6: # Ping role for Severe Delays or worse
                        alert_priority = True
                else:
                    good_service_names.append(name)

            # ONLY send if an actual change was detected
            if state_changed:
                if disrupted_messages:
                    final_message = "\n\n".join(disrupted_messages)
                    if good_service_names:
                        # Grouping good service lines into one line as requested
                        line_list = ", ".join(good_service_names)
                        final_message += f"\n\n✅ **Good service on all other lines:** ({line_list})"
                else:
                    final_message = "✅ **All Tube and DLR lines are now reporting a Good Service.**"

                send_to_discord(final_message, should_ping=alert_priority)
                last_heartbeat = current_time
            
            # 3-Hour Heartbeat (Silent check-in)
            elif (current_time - last_heartbeat) >= HEARTBEAT_INTERVAL:
                send_to_discord("🕒 *3-Hour Heartbeat: No changes detected. Script is active.*")
                last_heartbeat = current_time

        print(f"[{time.strftime('%H:%M:%S')}] Check complete. Sleeping 5 mins.")
        time.sleep(300)
