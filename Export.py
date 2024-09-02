import os
from datetime import datetime
import pandas as pd

def write_hierarchy_to_excel(kritis):
    result_dir = 'result'
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    timestamp = datetime.now().strftime('%Y_%m_%d_%H-%M-%S')
    filename = os.path.join(result_dir, f'kritis_hierarchy_{timestamp}.xlsx')

    all_data = []

    for eusector in kritis.eusectors:
        for sector in eusector.children:  # Anpassung hier
            for subsector in sector.children:  # Anpassung hier
                for entity in subsector.children:  # Anpassung hier
                    for company in entity.children:  # Anpassung hier
                        all_data.append([
                            eusector.name,
                            sector.name,
                            subsector.name,
                            entity.name,
                            company.name,
                            company.employee_amount,
                            company.revenue,
                            "Ja" if company.is_estimated else "Nein",
                            company.nis2_relevance_level,
                            company.chatgpt  # Angepasst von 'category' zu 'chatgpt'
                        ])

    df = pd.DataFrame(all_data, columns=[
        'EU Sektor',
        'Sektor',
        'Sub-Sektor',
        'Entität',
        'Unternehmen',
        'Mitarbeiterzahl',
        'Umsatz',
        'Geschätzt',
        'NIS2-Relevanz-Stufe', 
        'ChatGPT-Attribut'  # Spalte für das ChatGPT-Attribut (ehemals Kategorie)
    ])

    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Alle Daten', index=False)

    print(f'Daten wurden in {filename} geschrieben.')