from openai import OpenAI
import time
from dotenv import load_dotenv
import os

API_KEY = None

def load_api_key_once():
    print("load APIKEY")
    load_dotenv()  # Load environment variables from .env file
    api_key = os.getenv('OPENAI_API_KEY')
    return api_key

def initialize_openai_client():
    print("init APIKEY")
    if API_KEY is None:
        api_key = load_api_key_once()  # Load the API key only once
        openai_client = OpenAI(api_key=api_key)  # Initialize the OpenAI client
    return openai_client

def get_company_data_from_api(company_names):
    print("API")
    client = initialize_openai_client()
    print("API KEY loaded")
    prompt = (
        "Für die folgenden Unternehmen benötige ich präzise Daten in der folgenden Struktur: "
        "Name | Mitarbeiterzahl | Umsatz | Kritische Infrastruktur Kategorie\n"
        "Die Tabelle sollte keine Kopfzeilen enthalten. "
        "Die Mitarbeiterzahl sollte als ganze Zahl ohne Tausendertrennzeichen ausgegeben werden. "
        "Der Umsatz sollte ebenfalls als ganze Zahl ohne Abkürzungen oder Tausendertrennzeichen angegeben werden, in Euro. "
        "Fundierte Zahlen sollen ohne Minuszeichen angegeben werden."
        "Falls keine fundierten Zahlen verfügbar sind, geben Sie bitte die geschätzten Werte mit einem '-' vor der Zahl an. Zum Beispiel, wenn die geschätzte Mitarbeiterzahl 150 beträgt, soll dies als '-150' angezeigt werden."
        "Es gibt keine Unternehmen mit einer Mitarbeiterzahl von 0."
        "Die Geschätzte Kritische Infrastruktur Kategorie soll angeben, ob das Unternehmen zu NIS2 Annex 1, NIS2 Annex 2, keiner Kategorie oder einer anderen Kategorie gehört."
        "Die Daten sollen wie folgt formatiert sein:\n"
        "\n"
        "Name | Mitarbeiterzahl | Umsatz | Geschätzte Kategorie\n"
        "Unternehmen1 | 1000 | 50000000 | NIS2 Annex 1\n"
        "Unternehmen2 | -10 | 50000 | Keine Kategorie\n"
        "\n"
        "Hier sind die Unternehmen:\n"
        f"{', '.join(company_names)}\n"
        "\n"
        "Bitte gib die Daten genau im obigen Format zurück, ohne zusätzliche Kommentare oder Erklärungen. "
    )
    
    messages = [
        {"role": "system", "content": "You are a sales research assistant with knowledge about Cybersecurity"},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    time.sleep(21)
    print(company_names) 
    return response.choices[0].message.content.strip()

def parse_company_data(api_data):
    print("parser API company")
    company_data = {}
    lines = api_data.splitlines()

    for line in lines:
        if line.strip():
            parts = line.split('|')
            if len(parts) != 4:
                continue  # Skip lines that do not have exactly 4 parts
            
            name = parts[0].strip()
            employees = parts[1].strip()
            revenue = parts[2].strip()
            chatgpt = parts[3].strip()  # NIS2 Kategorie
            
            is_estimated = employees.startswith('-') or revenue.startswith('-')
            employee_int = int(employees.lstrip('-')) if employees.strip() and employees.lstrip('-').isdigit() else 0
            revenue_int = int(revenue.lstrip('-')) if revenue.strip() and revenue.lstrip('-').isdigit() else 0

            company_data[name] = {
                "employees": employee_int,
                "revenue": revenue_int,
                "is_estimated": is_estimated,
                "chatgpt": chatgpt  # Speichern der NIS2 Kategorie
            }
    print("Parser")
    return company_data

def generate_company_names(entity_name):
    """
    Generiert Unternehmensnamen basierend auf einem Entitätsnamen und gibt diese als Liste zurück.

    Args:
        entity_name (str): Der Name der Entität.

    Returns:
        list: Eine Liste von Unternehmensnamen.
    """
    client = initialize_openai_client()

    # Erstelle den Prompt für die API-Anfrage
    prompt = (
        "Für die folgende Entität benötige ich Unternehmensnamen, die diesem Unternehmensbereich entsprechen."
        "Die Liste soll aus Unternehmen bestehen die ausschließlich in Deutschland sitzen und sich auf keinen Fall doppeln."
        "Die Liste soll keinen Header haben und einfach untereinander aufgereiht werden."
        "Es sollen wirklich alle Unternehmen enthalten sein, sowohl die kleinsten als auch die groessten Unternehmen."
        "Die Struktur soll besipielsweise folgendermassen aussehen:"
        "Stadtwerke Troisdorf"
        "Siemens AG"
        "Bitte gib eine Liste von diesen Unternehmensnamen zurück, einen pro Zeile, ohne zusätzliche Kommentare oder Erklärungen:\n"
        f"{entity_name}\n"
    )

    # Sende die Anfrage an die API
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Du bist ein Web Crawler, der präzise arbeitet."},
            {"role": "user", "content": prompt}
        ]
    )
    time.sleep(21)
    print(response.choices[0].message['content'].strip())
    return response.choices[0].message['content'].strip()