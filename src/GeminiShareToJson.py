import json
import os
import subprocess
import time

CHAT_URLS = [
    "https://gemini.google.com/share/24d404e01359", "https://gemini.google.com/share/3aed870c4759",
    "https://gemini.google.com/share/15b72300acea", "https://gemini.google.com/share/f751386938e4",
    "https://gemini.google.com/share/01636cef2bc4", "https://gemini.google.com/share/696891242387",
    "https://gemini.google.com/share/efa5465d314a", "https://gemini.google.com/share/090ed53dace5",
    "https://gemini.google.com/share/e1fcc235c092", "https://gemini.google.com/share/928f080dcc2d",
    "https://gemini.google.com/share/89a98b37301c", "https://gemini.google.com/share/a70e4bf5e0e4",
    "https://gemini.google.com/share/1fb0dea1a203", "https://gemini.google.com/share/9d5404f5acd9",
    "https://gemini.google.com/share/fdfd471177d1", "https://gemini.google.com/share/da6616327c98",
    "https://gemini.google.com/share/d2c7cdf19ec4"
]

OUTPUT_DIR = "/Users/folkertmeeuw/PycharmProjects/neo4j-urmoses/data"


def get_safari_text(url):
    """Nutzt AppleScript, um den Text aus Safari zu extrahieren."""
    script = f'''
    tell application "Safari"
        set the URL of front document to "{url}"
        delay 5 -- Wartezeit für JavaScript-Laden
        set theText to text of front document
        return theText
    end tell
    '''
    try:
        proc = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        return proc.stdout
    except Exception as e:
        print(f"Fehler bei {url}: {e}")
        return ""


def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Safari muss aktiv sein und ein Fenster offen haben
    print("Bitte stelle sicher, dass Safari geöffnet ist.")

    for url in CHAT_URLS:
        url_id = url.split('/')[-1]
        output_path = os.path.join(OUTPUT_DIR, f"{url_id}.json")

        print(f"Safari extrahiert: {url}...")
        raw_text = get_safari_text(url)

        if len(raw_text) > 100:
            # Wir speichern den gesamten Textblock als Konversation
            chat_data = [{"role": "scraped_content", "content": raw_text.strip()}]

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({"url": url, "conversation": chat_data}, f, ensure_ascii=False, indent=4)
            print(f"✅ Erfolg: {url_id}.json")
        else:
            print(f"❌ Fehler: Kein Inhalt für {url_id} erhalten.")


if __name__ == "__main__":
    main()