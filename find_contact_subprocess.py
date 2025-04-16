# find_contact_subprocess.py
import subprocess
import csv
import os

def extract_contacts_to_csv(csv_path="contacts_output.csv"):
    script = '''
    tell application "Contacts"
        set output to ""
        repeat with p in people
            try
                set fullName to name of p as string
            on error
                set fullName to "Unnamed"
            end try

            try
                if phones of p is not {} then
                    set phoneVal to value of item 1 of phones of p as string
                else
                    set phoneVal to ""
                end if
            on error
                set phoneVal to ""
            end try

            set output to output & fullName & tab & phoneVal & linefeed
        end repeat
        return output
    end tell
    '''

    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)

    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError("AppleScript failed or returned no data")

    rows = []
    for line in result.stdout.strip().splitlines():
        if line.strip():
            parts = line.strip().split("\t")
            if len(parts) == 2:
                rows.append({"Name": parts[0], "Phone": parts[1]})

    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["Name", "Phone"])
        writer.writeheader()
        writer.writerows(rows)

    return csv_path

if __name__ == "__main__":
    path = extract_contacts_to_csv()
    print(f"✅ Contacts exported to {path}")
