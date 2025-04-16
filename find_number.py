import csv
import difflib
import os

def lookup_contact(query_name: str, csv_path: str = None) -> str:
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(__file__), 'contacts_output.csv')

    # Load contacts from CSV
    contacts = []
    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row.get("Name", "").strip()
            phone = row.get("Phone", "").strip()
            if name:
                contacts.append({"name": name, "phone": phone})

    if not query_name.strip():
        return ""

    # Build list of contact names
    names = [c['name'] for c in contacts]

    # Find the closest match using difflib
    matches = difflib.get_close_matches(query_name, names, n=1, cutoff=0.6)

    if matches:
        best = matches[0]
        # Retrieve the corresponding phone number
        return next((c['phone'] for c in contacts if c['name'] == best), '')
    else:
        return ""

# Example usage
if __name__ == "__main__":
    user_input = input("🔍 Enter a name: ").strip()
    phone = lookup_contact(user_input)
    print(phone or "❌ No close match found.")
