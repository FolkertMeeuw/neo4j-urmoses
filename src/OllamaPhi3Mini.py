import ollama
from ollama import Client

# Konfiguration auf das vorhandene Leichtgewicht-Modell
MODEL = 'phi3:mini'
PROMPT = "Extrahiere Abhängigkeiten als A->B aus: Der Launch kann erst erfolgen, wenn das Backend-Audit durch ist."


def run_extraction():
    # Timeout hoch, da 8GB RAM beim Laden des Modells langsam sein können
    client = Client(host='http://127.0.0.1:11434', timeout=120)

    try:
        print(f"Kontaktiere {MODEL}...")
        response = client.chat(
            model=MODEL,
            messages=[{'role': 'user', 'content': PROMPT}],
            options={
                "num_ctx": 4096,  # Phi3 verträgt etwas mehr Kontext als Llama3 bei weniger RAM
                "num_thread": 4
            }
        )
        print("\nGefundene Relationen:")
        print(response['message']['content'])

    except Exception as e:
        print(f"\nFehler: {e}")


if __name__ == "__main__":
    run_extraction()