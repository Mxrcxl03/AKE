from FileHandler import FileHandler
from OpenAI_Integration import parse_company_data, get_company_data_from_api
from Export import write_hierarchy_to_excel
from Datamodel import load_json_from_file, create_structure_from_json
import time

start_zeit = time.time()

json_data = load_json_from_file('dictionary.json')
file_handler = FileHandler()
file_handler.parseConfigFile()

end_zeit = time.time()
benoetigte_zeit = end_zeit - start_zeit
print(f"Das Programm hat {benoetigte_zeit:.4f} Sekunden benötigt.")

data = file_handler.getCurrentData()
#print(data)
#data = [["Aggregierung Laststeuerung", ["Lufthansa", "TUIFly", "Ryanair","Germanwings", "Stadtwerke Troisdorf"]], ["Verteilernetzbetreiber", ["Lufthansa", "TUIFly", "Ryanair","Germanwings"]]]
# Create structure from JSON and additional company data

start_zeit = time.time()

infrastructure = create_structure_from_json(json_data, data)
infrastructure.display()
write_hierarchy_to_excel(infrastructure)

end_zeit = time.time()
benoetigte_zeit = end_zeit - start_zeit
print(f"Das Programm hat {benoetigte_zeit:.4f} Sekunden benötigt.")