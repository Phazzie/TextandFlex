import pandas as pd
import random
from datetime import datetime, timedelta

# Create sample data
data = []
phone_numbers = ["6180930000", "7297250000", "2693325851", "2695879231", "2694215838", "8460400000", "2693268024"]
start_date = datetime(2025, 1, 20)

# Generate 50 records
for i in range(50):
    record_date = start_date + timedelta(days=random.randint(0, 10))
    record_time = datetime.strptime(f"{random.randint(0, 23)}:{random.randint(0, 59)}", "%H:%M")
    formatted_date = record_date.strftime("%m/%d/%Y")
    formatted_time = record_time.strftime("%I:%M %p")
    
    data.append({
        "Line": "2693037499",
        "Date": formatted_date,
        "Time": formatted_time,
        "Direction": "Received",
        "To/From": random.choice(phone_numbers),
        "Message Type": "Text"
    })

# Create DataFrame
df = pd.DataFrame(data)

# Save to Excel
df.to_excel("test_data/sample_phone_records.xlsx", index=False)

print("Test data created successfully!")
