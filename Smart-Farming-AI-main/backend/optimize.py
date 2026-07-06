import requests
import google.generativeai as genai
import time
import re
from datetime import datetime
import csv
from io import StringIO


# Configuration
SHEET_URL = "Your_Sheet_URL"
GEMINI_API_KEY = "Your_API_Key" 
TARGET_MOISTURE_RAW = 500  
CHECK_INTERVAL = 30  

# ---------------- Google Sheets Setup ---------------- #
def setup_google_sheets(sheet_url):
    """Read public Google Sheet as CSV without authentication."""
    try:
        print(f"📥 Fetching data from: {sheet_url}")
        response = requests.get(sheet_url)
        response.raise_for_status()
        
        print("✅ Successfully loaded public sheet!")
        return response.text
    except Exception as e:
        print(f"❌ Error connecting to Google Sheets: {e}")
        return None

# ---------------- Gemini AI Setup ---------------- #
def setup_gemini(api_key):
    """Set up the Gemini AI model."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        print("✅ Gemini AI configured successfully!")
        return model
    except Exception as e:
        print(f"❌ Error setting up Gemini: {e}")
        return None

# ---------------- Sheet Data Reading ---------------- #
def get_new_sensor_data(csv_data):
    """
    Get all sensor data from the CSV data with exact column names.
    """
    try:
        csv_file = StringIO(csv_data)
        reader = csv.DictReader(csv_file)
        print("🧾 CSV Columns detected:", reader.fieldnames)

        
        # Use exact column names from your sheet
        moisture_col = 'Moisture (%)'
        temp_col = 'Temperature (°C)'
        humidity_col = 'Humidity (%)'
        source_col = 'SourceRowID'
        
        new_data = []
        for i, row in enumerate(reader, start=2):
            try:
                # Convert raw moisture value (0-1023 scale) to meaningful value
                raw_moisture = float(row[moisture_col])
                temperature = float(row[temp_col])
                humidity = float(row[humidity_col]) if humidity_col in row else 0
                source_row_id = row.get(source_col, f"Row {i}")
                
                new_data.append((i, raw_moisture, temperature, source_row_id))
                print(f"   📊 Row {i}: Moisture_RAW={raw_moisture}, Temp={temperature}°C")
                
            except ValueError as e:
                print(f"⚠️  Invalid number in row {i}: {e}")
            except Exception as e:
                print(f"⚠️  Error processing row {i}: {e}")
        
        print(f"📈 Found {len(new_data)} valid data rows")
        return new_data
    except Exception as e:
        print(f"❌ Error reading CSV data: {e}")
        return []

# ---------------- AI Prompt & Response ---------------- #
def create_ai_prompt(raw_moisture, temperature, target_moisture=500):
    """
    Updated prompt for 0-1023 moisture scale where:
    - Higher values = Drier soil (0 = very wet, 1023 = very dry)
    - Target around 500 = optimal moisture
    """
    return f"""
You are a smart farming irrigation expert. Analyze the soil moisture and temperature data to determine whether to turn the water pump ON or OFF and for how long.

SENSOR SCALE EXPLANATION:
- Moisture sensor uses 0-1023 scale (NOT percentage)
- 0 = Very Wet, 1023 = Very Dry
- Target moisture level: {target_moisture}
- Current moisture reading: {raw_moisture}

CURRENT CONDITIONS:
- Current Soil Moisture (Raw): {raw_moisture} (0-1023 scale, lower=wetter)
- Current Temperature: {temperature}°C
- Target Moisture Level: {target_moisture}
- Maximum Watering Duration: 15 minutes

IRRIGATION RULES (0-1023 scale):
1. Base watering on moisture reading:
   - Below 300: Very wet - PUMP OFF, 0 minutes
   - 300-450: Adequate moisture - PUMP OFF, 0-2 minutes
   - 450-550: Slightly dry - PUMP ON, 3-6 minutes  
   - 550-700: Dry - PUMP ON, 7-10 minutes
   - Above 700: Very dry - PUMP ON, 11-15 minutes

2. Adjust for temperature (current: {temperature}°C):
   - Below 20°C: Reduce watering by 1-2 minutes
   - 20-30°C: Normal watering
   - 30-40°C: Increase watering by 1-3 minutes
   - Above 40°C: Increase watering by 2-4 minutes

3. Always minimize water waste while ensuring plant health.

REQUIRED OUTPUT FORMAT:
PUMP: [ON/OFF]
DURATION: [number between 0-15] minutes
JUSTIFICATION: [Two-sentence explanation mentioning both moisture and temperature factors]

Now analyze the current conditions and provide your recommendation:
"""

def extract_ai_response(response_text):
    """Extract pump status, duration and justification from AI response with safety checks."""
    try:
        # Look for PUMP status
        pump_match_on = re.search(r'PUMP:\s*ON', response_text, re.IGNORECASE)
        pump_match_off = re.search(r'PUMP:\s*OFF', response_text, re.IGNORECASE)
        
        if pump_match_on:
            pump_status = "ON ⚡"
        elif pump_match_off:
            pump_status = "OFF ❌"
        else:
            # Fallback: if no explicit PUMP status, determine from duration
            duration_match = re.search(r'DURATION:\s*(\d+)', response_text, re.IGNORECASE)
            if duration_match:
                duration_val = int(duration_match.group(1))
                pump_status = "ON ⚡" if duration_val > 0 else "OFF ❌"
            else:
                pump_status = "OFF ❌"  # Default safe option

        # Look for duration pattern
        duration_match = re.search(r'DURATION:\s*(\d+)', response_text, re.IGNORECASE)
        if not duration_match:
            duration_match = re.search(r'(\d+)\s*minutes?', response_text, re.IGNORECASE)
        
        duration = int(duration_match.group(1)) if duration_match else 0

        # Look for justification
        justification_match = re.search(r'JUSTIFICATION:\s*(.*?)(?:\n\n|\nPUMP:|\nDURATION:|$)', response_text, re.IGNORECASE | re.DOTALL)
        if not justification_match:
            justification_match = re.search(r'JUSTIFICATION:\s*(.*)', response_text, re.IGNORECASE | re.DOTALL)
        
        justification = justification_match.group(1).strip() if justification_match else "No justification provided."

        # Safety checks
        duration = max(0, min(15, duration))
        
        # Ensure consistency: if PUMP is OFF, duration should be 0
        if pump_status == "OFF ❌":
            duration = 0
            
        return pump_status, duration, justification
    except Exception as e:
        print(f"❌ Error parsing AI response: {e}")
        return "OFF ❌", 0, "Error processing AI response. Using safe default of no watering."

def get_irrigation_decision():
    return get_latest_irrigation_decision_once()


def get_latest_irrigation_decision_once():
    csv_data = setup_google_sheets("Your_Sheet_URL")
    if not csv_data:
        return None

    model = setup_gemini("Your_API_Key"
    if not model:
        return None

    data = get_new_sensor_data(csv_data)
    if not data:
        return None

    # take ONLY the latest row
    _, raw_moisture, temperature, _ = data[-1]

    prompt = create_ai_prompt(raw_moisture, temperature, TARGET_MOISTURE_RAW)
    response = model.generate_content(prompt)

    pump, duration, justification = extract_ai_response(response.text)
    print("✅ FINAL DECISION:", pump, duration, justification)


    return {
        "moisture": raw_moisture,
        "temperature": temperature,
        "pump": "ON" if "ON" in pump else "OFF",
        "duration": f"{duration} minutes",
        "justification": justification
    }


# ---------------- Main Processing ---------------- #
def process_sensor_readings(csv_data, model):
    """Process all readings and print watering recommendations."""
    data = get_new_sensor_data(csv_data)
    if not data:
        print("📭 No valid data found in sheet.")
        return

    print(f"\n💧 Processing {len(data)} sensor readings...")
    
    for row_number, raw_moisture, temperature, source_row_id in data:
        print(f"\n" + "="*60)
        print(f"🔍 Processing {source_row_id}")
        print(f"📊 Sensor Data - Moisture_RAW: {raw_moisture}, Temperature: {temperature}°C")
        
        # Determine soil condition for display
        if raw_moisture < 300:
            condition = "💧 VERY WET"
        elif raw_moisture < 450:
            condition = "💧 Adequate"
        elif raw_moisture < 550:
            condition = "🌱 Slightly Dry"
        elif raw_moisture < 700:
            condition = "⚠️ Dry"
        else:
            condition = "🚨 VERY DRY"
        
        print(f"🌱 Soil Condition: {condition}")
        
        prompt = create_ai_prompt(raw_moisture, temperature, TARGET_MOISTURE_RAW)
        
        try:
            response = model.generate_content(prompt)
            ai_response = response.text
            print(f"🤖 AI Raw Response:\n{ai_response}")
        except Exception as e:
            print(f"❌ Error getting AI response: {e}")
            continue

        pump_status, duration, justification = extract_ai_response(ai_response)
        
        print(f"🔧 PUMP ACTION: {pump_status}")
        if pump_status == "ON ⚡":
            print(f"⏰ WATERING DURATION: {duration} minutes")
        else:
            print(f"⏰ WATERING DURATION: {duration} minutes (No watering)")
        print(f"💡 JUSTIFICATION: {justification}")

# ---------------- Main Loop ---------------- #
def main_loop():
    print("🚀 Starting Smart Farming: AI-Powered Irrigation System")
    print(f"💧 Target Moisture Level: {TARGET_MOISTURE_RAW} (0-1023 scale)")
    print(f"🤖 Using: Gemini AI for Pump ON/OFF decisions")
    print(f"🔄 Check Interval: {CHECK_INTERVAL} seconds")
    
    # Test the sheet connection first
    print("\n🔗 Testing Google Sheets connection...")
    csv_data = setup_google_sheets(SHEET_URL)
    if not csv_data:
        print("❌ Failed to connect to Google Sheets.")
        return

    print("\n🤖 Setting up Gemini AI...")
    model = setup_gemini(GEMINI_API_KEY)
    if not model:
        print("❌ Failed to setup Gemini AI. Please check your API key.")
        return

    print(f"\n✅ All systems ready! Starting AI-powered monitoring...")
    print("Press Ctrl+C to stop the program\n")
    
    while True:
        print(f"\n⏰ Check initiated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            # Refresh data each time
            csv_data = setup_google_sheets(SHEET_URL)
            if csv_data:
                process_sensor_readings(csv_data, model)
            else:
                print("❌ Could not fetch updated data")
        except Exception as e:
            print(f"❌ Error in main processing: {e}")
        
        print(f"\n⏳ Waiting {CHECK_INTERVAL} seconds until next check...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n🛑 Script interrupted by user. Exiting...")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
