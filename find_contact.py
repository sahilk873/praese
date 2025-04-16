import sqlite3
import os

# Path to the Contacts database
contacts_db_path = os.path.expanduser("~/Library/Application Support/AddressBook/AddressBook-v22.abcddb")

# Connect to the database
conn = sqlite3.connect(contacts_db_path)
cursor = conn.cursor()

# Query all contact names + phone numbers + emails
query = '''
SELECT ZABCDRECORD.Z_PK, ZABCDRECORD.ZFIRSTNAME, ZABCDRECORD.ZLASTNAME, ZABCDPHONENUMBER.ZFULLNUMBER, ZABCDEMAILADDRESS.ZADDRESS
FROM ZABCDRECORD
LEFT JOIN ZABCDPHONENUMBER ON ZABCDPHONENUMBER.ZOWNER = ZABCDRECORD.Z_PK
LEFT JOIN ZABCDEMAILADDRESS ON ZABCDEMAILADDRESS.ZOWNER = ZABCDRECORD.Z_PK
'''

cursor.execute(query)
rows = cursor.fetchall()

# Collect and print all contacts
print("\n📇 Contacts Found:")
contacts = []
for row in rows:
    pk, first, last, phone, email = row
    full_name = f"{first or ''} {last or ''}".strip()
    if not full_name:
        continue

    contact_info = {
        "name": full_name,
        "phone": phone,
        "email": email
    }
    contacts.append(contact_info)
    print(f"- {full_name} | 📞 {phone or '—'} | ✉️ {email or '—'}")

# Ask user to search for a contact name
target = input("\n🔍 Enter a name to look up the phone/email: ").lower()

# Show all matches
print("\n✅ Matches:")
found = False
for c in contacts:
    if target in c["name"].lower():
        found = True
        print(f"👤 {c['name']}\n   📞 {c['phone'] or '—'}\n   ✉️ {c['email'] or '—'}")

if not found:
    print("❌ No match found.")

conn.close()
