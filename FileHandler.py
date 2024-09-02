import urllib.request
import ssl
import os
import csv
import glob
import openpyxl  # Für das Lesen von Excel-Dateien
import pdfplumber  # Für das Lesen von PDF-Dateien
import json
from OpenAI_Integration import generate_company_names
from datetime import datetime

class FileHandler:
    def __init__(self):
        # Erstellen eines plattformunabhängigen Pfads
        self.config_file_name = 'import.cfg'
        self.download_folder = 'downloads'
        self.list_folder = 'lists'
        self.loaded_folder = 'loaded'
        os.makedirs(self.list_folder, exist_ok=True)  # Erstellt das Verzeichnis, falls es nicht existiert
        os.makedirs(self.loaded_folder, exist_ok=True)  # Erstellt das Verzeichnis, falls es nicht existiert
        os.makedirs(self.download_folder, exist_ok=True)  # Erstellt das Verzeichnis, falls es nicht existiert

    def __downloadFileFromUrl(self, file_url, file_path):
        """
        Lädt eine Datei von einer angegebenen URL herunter und speichert sie in einem angegebenen Verzeichnis mit einem angegebenen Dateinamen.

        Args:
        file_url (str): Die URL der Datei, die heruntergeladen werden soll.
        file_path (str): Der Pfad, Name und Endung der herunterzuladenden Datei.

        Returns:
        int: 0 für keinen Fehler und 1 wenn es einen Fehler gab
        """
        # SSL-Zertifikatsprüfung deaktivieren
        ssl._create_default_https_context = ssl._create_unverified_context

        # Herunterladen der Datei
        try:
            urllib.request.urlretrieve(file_url, file_path)
            print(f'Datei erfolgreich heruntergeladen und gespeichert als {file_path}')
            return 0
        except Exception as e:
            print(f'Fehler beim Herunterladen der Datei: {e}')
            return 1

    def __replace_special_characters(self, text):
        replacements = {
            'ä': 'ae', 'Ä': 'Ae',
            'ö': 'oe', 'Ö': 'Oe',
            'ü': 'ue', 'Ü': 'Ue',
            'ß': 'ss', '°': '', '"':  '', '*' : '',
            'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'å': 'a',
            'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
            'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
            'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'oe',
            'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'ue',
            'ý': 'y', 'ÿ': 'y',
            '\n': '', '\r': ''
        }

        for key, value in replacements.items():
            text = text.replace(key, value)
    
        return text

    def __extractDataFromExcel(self, file_path, data_column, skip_rows, skip_on_all):
        data = []
        # Lade die Excel-Datei
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active  # Oder wähle ein bestimmtes Blatt aus
        
        # Iteriere über die Zeilen in der angegebenen Spalte (data_column)
        for i, row in enumerate(sheet.iter_rows(min_col=data_column + 1, max_col=data_column + 1, values_only=True)):
            if i < skip_rows:
                continue
            cell_value = row[0]  # Der Wert in der angegebenen Spalte
            if cell_value is not None:
                # Ersetze spezielle Zeichen in der Zielspalte
                cleaned_text = self.__replace_special_characters(str(cell_value))
                data.append(cleaned_text)
        
        return data

    def __extractDataFromPdf(self, file_path, data_column, skip_rows, skip_on_all):
        data = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    # Führe nur auf der ersten Seite aus, wenn skip_on_all = 0
                    for row in table[((page.page_number == 1) or skip_on_all) * skip_rows:]:
                        # Ersetze spezielle Zeichen in der Zielspalte
                        cleaned_text = self.__replace_special_characters(row[data_column])
                        data.append(cleaned_text)
        return data

    def __extractDataFromCsv(self, file_path, data_column, skip_rows):
        data = []
        with open(file_path, 'r', encoding='utf-8') as file:
            csvreader = csv.reader(file, delimiter=';')
            # Überspringe die ersten skip_rows Zeilen
            for i, row in enumerate(csvreader):
                if i < skip_rows:
                    continue
                if len(row) > data_column:
                    # Ersetze spezielle Zeichen in der Zielspalte
                    cleaned_text = self.__replace_special_characters(row[data_column])
                    data.append(cleaned_text)
        return data

    def __extractDataFromFile(self, file_path, file_type, data_column, skip_rows, skip_on_all):
        if file_type == 'pdf':
            return self.__extractDataFromPdf(file_path, data_column, skip_rows, skip_on_all)
        elif file_type == 'xlsx':
            return self.__extractDataFromExcel(file_path, data_column, skip_rows, skip_on_all)
        elif file_type == 'csv':
            return self.__extractDataFromCsv(file_path, data_column, skip_rows)
        else:
            print(f"Unbekannter Dateityp {file_type}")
            return []

    def __writeDataToTxtFile(self, folder, file_name, data):
        """
        Schreibt die Daten in eine .txt-Datei in einem angegebenen Ordner.

        Args:
        folder (str): Der Ordner, in dem die Datei gespeichert werden soll.
        file_name (str): Der Name der .txt-Datei, ohne Endung.
        data (list): Eine Liste von Strings, die in die Datei geschrieben werden sollen.
        """
        # Vorbereiten des Dateinamens
        file_path = os.path.join(folder, file_name + '.txt')
        
        # Datei im Schreibmodus öffnen (überschreibt die Datei, wenn sie bereits existiert)
        with open(file_path, 'w', encoding='utf-8') as file:
            for line in data:
                file.write(line + '\n')  # \n fügt einen Zeilenumbruch hinzu

        print(f'Die Datei {file_path} wurde erfolgreich geschrieben.')

    def __convertExistingFile(self, file_path, file_type, data_column, skip_rows):
        """
        Konvertiert eine vorhandene Datei in eine .txt-Datei und speichert sie im loaded-Ordner.

        Args:
        file_path (str): Der Pfad zur vorhandenen Datei.
        file_type (str): Der Dateityp (pdf, xlsx, csv).
        data_column (int): Die Spalte, aus der die Daten extrahiert werden sollen.
        skip_rows (int): Die Anzahl der zu überspringenden Zeilen.
        """
        name_list = self.__extractDataFromFile(file_path, file_type, data_column, skip_rows, False)
        
        # Entferne das "_raw" Suffix aus dem Dateinamen
        file_name = os.path.splitext(os.path.basename(file_path))[0].replace('_raw', '')
        
        self.__writeDataToTxtFile(self.loaded_folder, file_name, name_list)

    def parseConfigFile(self):
        """
        Öffnet die Import-Konfigurationsdatei, lädt die hinterlegten Dateien runter 
        und erzeugt die .txt-Dateien neu. Wenn kein Link vorhanden ist, wird die bestehende Datei verwendet.

        Returns:
        int: 0 für keinen Fehler und 1 wenn die Konfigurationsdatei nicht gefunden wurde
        """
        try:
            with open(self.config_file_name, 'r') as config_file:
                csvreader_config = csv.reader(config_file, delimiter=';')
                # Überspringen der ersten Zeile, da hier die Überschriften stehen
                config_header = next(csvreader_config)
                # Ab der zweiten Zeile beginnen die Einträge der Datei
                for row in csvreader_config:
                    if len(row) < 6:
                        print(f"Fehler: Die Zeile hat nicht die erwartete Anzahl von Werten: {row}")
                        continue

                    entity_name, file_type, data_column, skip_rows, skip_on_all, file_url = row

                    # Konvertiere die Werte in die entsprechenden Typen
                    data_column = int(data_column)
                    skip_rows = int(skip_rows)
                    skip_on_all = bool(int(skip_on_all))

                    # Vorbereiten des Dateinamens
                    download_file_path = os.path.join(self.download_folder, entity_name + '_raw.' + file_type)

                    if file_url:
                        # Datei herunterladen
                        if self.__downloadFileFromUrl(file_url, download_file_path) == 0:
                            # Wenn der Download erfolgreich war, Daten extrahieren und in .txt-Datei im loaded-Ordner schreiben
                            name_list = self.__extractDataFromFile(download_file_path, file_type, data_column, skip_rows, skip_on_all)
                            self.__writeDataToTxtFile(self.loaded_folder, entity_name, name_list)
                    else:
                        # Wenn kein Link vorhanden ist, verarbeite die vorhandene Datei
                        if os.path.exists(download_file_path):
                            self.__convertExistingFile(download_file_path, file_type, data_column, skip_rows)
                        else:
                            print(f"Keine URL und keine vorhandene Datei für {entity_name} gefunden.")

                return 0
        except FileNotFoundError:
            print("Die Konfigurationsdatei wurde nicht gefunden.")
            return 1
        
    def getCurrentData(self):
        """
        Liest die aktuellen Daten aus allen .txt-Dateien im lists- und loaded-Verzeichnis.

        Returns:
        list: Eine Liste von Tupeln, wobei jedes Tupel aus dem Dateinamen (ohne Endung) und einer Liste von Zeilen besteht.
        """
        data = []
        for folder in [self.list_folder, self.loaded_folder]:
            for file_path in glob.glob(os.path.join(folder, '*.txt')):
                file_name = os.path.splitext(os.path.basename(file_path))[0]
                with open(file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                    lines = [line.strip() for line in lines]
                    data.append((file_name, lines))
        return data

    def read_json(self, json_file):
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    def get_existing_files(self):
        """
        Liest die existierenden .txt-Dateien aus dem `loaded`-Ordner.
        """
        existing_files = {os.path.splitext(f)[0] for f in os.listdir(self.loaded_folder) if f.endswith('.txt')}
        return existing_files

    def extract_entities(self, data):
        entities_list = []

        # Iteriere durch alle Sektoren und deren Subsektoren
        sectors = data.get("EuSektoren", {}).get("Nis2Annex1", {}).get("Sectors", {})
        for sector, sector_details in sectors.items():
            subsectors = sector_details.get("Subsectors", {})
            for subsector, subsector_details in subsectors.items():
                entities = subsector_details.get("Entities", [])
                for entity in entities:
                    entities_list.append(entity)

        return entities_list

    def write_to_txt(self, entities_list, existing_files):
        for entity in entities_list:
            # Überspringe die Entität, wenn bereits eine Datei im `loaded`-Ordner existiert
            if entity in existing_files:
                print(f"Überspringe {entity}, da die Datei bereits im 'loaded'-Ordner existiert.")
                continue

            file_path = os.path.join(self.list_folder, f'{entity}.txt')
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(entity + '\n')
            print(f'Datei für {entity} wurde erfolgreich erstellt: {file_path}')

    def convert(self, json_file):
        data = self.read_json(json_file)
        entities_list = self.extract_entities(data)
        existing_files = self.get_existing_files()
        self.write_to_txt(entities_list, existing_files)

    def populate_txt_files(self):
        """
        Liest die Dateinamen aus dem 'lists'-Ordner, übergibt sie der API, und befüllt die Dateien mit den zurückgegebenen Daten.
        Erzeugt eine Log-Datei mit dem Datum und der Uhrzeit der letzten Aktualisierung.
        """
        # Durchlaufen der .txt-Dateien im lists-Ordner
        for file_path in glob.glob(os.path.join(self.list_folder, '*.txt')):
            # Extrahiere den Dateinamen ohne Endung
            print(file_path)
            entity_name = os.path.splitext(os.path.basename(file_path))[0]
            print(entity_name)
            # Generiere Unternehmensnamen über die API
            company_names = generate_company_names(entity_name)  # Ruft die API auf
            
            # Unternehmensnamen in die Datei schreiben
            with open(file_path, 'w', encoding='utf-8') as file:
                for name in company_names:
                    file.write(name + '\n')
            
            print(f'Datei {file_path} wurde erfolgreich befüllt.')

        # Erstelle oder aktualisiere die Log-Datei
        self.create_update_log_file()

    def create_update_log_file(self):
        """
        Erstellt eine Log-Datei mit dem Datum und der Uhrzeit der letzten Aktualisierung
        im Format 'update_YYYY-MM-DD_HH-MM-SS.log' im lists-Ordner.
        """
        now = datetime.now()
        timestamp = now.strftime('%Y-%m-%d_%H-%M-%S')
        log_file_name = f'update_{timestamp}.log'
        log_file_path = os.path.join(self.list_folder, log_file_name)

        # Erstelle oder überschreibe die Log-Datei
        with open(log_file_path, 'w', encoding='utf-8') as log_file:
            log_file.write(f'Daten zuletzt aktualisiert am: {now.strftime("%Y-%m-%d %H:%M:%S")}\n')
        
        print(f'Log-Datei erstellt: {log_file_path}')

"""def main():
    handler = FileHandler()
    handler.parseConfigFile()
    data = handler.getCurrentData()
    
    for file_name, lines in data:
        print(f"Inhalt der Datei '{file_name}.txt':")
        for line in lines:
            print(line)
        print()

if __name__ == "__main__":
    main()
def main():

    # Create an instance of FileHandler and process files
    handler = FileHandler()  # Correctly create an instance of FileHandler
    #handler.parseConfigFile()  # Call the parseConfigFile method
        # Create an instance of JSONToTxtConverter and convert the JSON file
    handler.convert('dictionary.json')

    handler.populate_txt_files
    # Retrieve the current data
    data = handler.getCurrentData()  # Call the getCurrentData method



    # Example of how to print the retrieved data (optional)
    #for file_name, lines in data:
     #   print(f"Inhalt der Datei '{file_name}.txt':")
        #for line in lines:
        #    print(line)
        #print()

if __name__ == "__main__":
    main()
"""