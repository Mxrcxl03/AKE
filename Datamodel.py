from FileHandler import FileHandler
from OpenAI_Integration import parse_company_data, get_company_data_from_api
from Export import write_hierarchy_to_excel
import json

class Company:
    def __init__(self, name, employee_amount, revenue, is_estimated=False, chatgpt=None):
        self.name = name
        self.employee_amount = employee_amount
        self.revenue = revenue
        self.is_estimated = is_estimated
        self.chatgpt = chatgpt  # New attribute for the NIS2 chatgpt
        self.nis2_relevance_level = self.calculate_nis2_relevance_level()

    def calculate_nis2_relevance_level(self):
        if self.revenue >= 50000000 or self.employee_amount >= 250:
            return 1
        elif self.revenue >= 10000000 or self.employee_amount >= 50:
            return 2
        else:
            return 0

    def display(self, depth=0):
        print(" " * depth + (
            f"{self.name} (Employees: {self.employee_amount}, Revenue: {self.revenue}, "
            f"Estimated: {self.is_estimated}, NIS2 Relevance Level: {self.nis2_relevance_level}, "
            f"chatgpt: {self.chatgpt})"
        ))

class HierarchicalEntity:
    def __init__(self, name):
        self.name = name
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def display(self, depth=0):
        print(" " * depth + self.name)
        for child in self.children:
            child.display(depth + 2)

class Sector(HierarchicalEntity):
    pass

class Subsector(HierarchicalEntity):
    pass

class Entity(HierarchicalEntity):
    def __init__(self, name, companies=None):
        super().__init__(name)
        self.companies = companies if companies is not None else []

    def add_company(self, company):
        self.add_child(company)

class EuSektor(HierarchicalEntity):
    pass

class Kritis:
    def __init__(self):
        self.eusectors = []

    def add_eu_sector(self, eusector):
        self.eusectors.append(eusector)

    def display(self, depth=0):
        print("Kritis")
        for sector in self.eusectors:
            sector.display(depth + 2)

def createCompaniesFromData(company_names):
    api_data = get_company_data_from_api(company_names)
    company_data = parse_company_data(api_data)
    companies = []
    for name in company_names:
        if name in company_data:
            data = company_data[name]
            company = Company(
                name,
                employee_amount=data.get("employees", 0), 
                revenue=data.get("revenue", 0),           
                is_estimated=data.get("is_estimated", False),
                chatgpt=data.get("chatgpt", "Unbekannt")  
            )
        else:
            company = Company(name, 0, 0, is_estimated=False, chatgpt="Unbekannt")
        companies.append(company)
    return companies

def add_companies_to_entity(entity, company_names):
    companies = createCompaniesFromData(company_names)
    for company in companies:
        entity.add_company(company)

def create_structure_from_json(json_data, additional_company_data):
    kritis = Kritis()

    def add_entities_to_subsector(subsector, entities_data, additional_data):
        print("add_entities_to_subsector")
        for entity_name in entities_data:
            entity = Entity(entity_name)
            for data_name, company_names in additional_data:
                if entity_name == data_name:
                    add_companies_to_entity(entity, company_names)
            subsector.add_child(entity)

    def add_subsectors_to_sector(sector, subsectors_data, additional_data):
        print("add_subsectors_to_sector")
        for subsector_name, subsector_info in subsectors_data.items():
            subsector = Subsector(subsector_name)
            add_entities_to_subsector(subsector, subsector_info.get("Entities", []), additional_data)
            sector.add_child(subsector)

    def add_sectors_to_eu_sector(eu_sector, sectors_data, additional_data):
        print("add_sectors_to_eu_sector")
        for sector_name, sector_info in sectors_data.items():
            sector = Sector(sector_name)
            add_subsectors_to_sector(sector, sector_info.get("Subsectors", {}), additional_data)
            eu_sector.add_child(sector)

    eusectors_data = json_data.get("EuSektoren", {})
    for eusector_name, eusector_info in eusectors_data.items():
        print("eusectors")
        eusector = EuSektor(eusector_name)
        add_sectors_to_eu_sector(eusector, eusector_info.get("Sectors", {}), additional_company_data)
        kritis.add_eu_sector(eusector)

    return kritis

def load_json_from_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)
    

# Load JSON data from file
json_data = load_json_from_file('dictionary.json')

file_handler = FileHandler()
file_handler.parseConfigFile()
data = file_handler.getCurrentData()
print(data)
#data = [["Aggregierung Laststeuerung", ["Lufthansa", "TUIFly", "Ryanair","Germanwings", "Stadtwerke Troisdorf"]], ["Verteilernetzbetreiber", ["Lufthansa", "TUIFly", "Ryanair","Germanwings"]]]
# Create structure from JSON and additional company data
#infrastructure = create_structure_from_json(json_data, data)
#infrastructure.display()
#write_hierarchy_to_excel(infrastructure)
