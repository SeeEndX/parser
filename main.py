import signal
import parser_logic.logic as l
import gui.views as v
import pandas as pd
import sys
import os

results = []

RESULTS_FILE = 'files/описание_шин.xlsx'

################################################ CHECKPOINT
def signal_handler(sig, frame):
    print("\nПолучен сигнал для завершения. Сохранение промежуточных результатов...")
    save_results()
    sys.exit(0)

def save_results():
    if results:
        results_df = pd.DataFrame(results)
        results_df.to_excel(RESULTS_FILE, index=False)
        print(f"Промежуточные результаты успешно сохранены в {RESULTS_FILE}")

def load_previous_results():
    if os.path.exists(RESULTS_FILE):
        print(f"Загрузка предыдущих результатов из {RESULTS_FILE}")
        return pd.read_excel(RESULTS_FILE).to_dict(orient='records')
    return []
################################################


def main():
    signal.signal(signal.SIGINT, signal_handler) 
    previous_results = load_previous_results()
    if previous_results:
        global results
        results = previous_results
    
    tires = l.parse_xml('files/tires.xml')
    proxies = l.load_proxies('files/proxies.txt')

    for tire in tires:
        brand = tire['brand']
        model = tire['product']

        if not model:
            print(f"Обнаружено отсутствие модели для бренда: {brand}")
            continue

        if l.already_processed(brand, model, previous_results):
            print(f"Шина {brand} {model} уже обработана, пропускаем...")
            continue

        description_drom = l.get_tyre_description_drom(brand, model, proxies)
        print(f"Описание с drom.ru для {brand} {model}: {description_drom}")
        
        results.append({
            'Название шины': f"{brand} {model}",
            'Описание drom.ru': description_drom,
            'Описание mosautoshina.ru': ''
        })
        save_results()

        description_mosautoshina = l.get_tyre_description_mosautoshina(brand, model, proxies)
        print(f"Описание с mosautoshina.ru для {brand} {model}: {description_mosautoshina}")

        for result in results:
            if result['Название шины'] == f"{brand} {model}":
                result['Описание mosautoshina.ru'] = description_mosautoshina

        save_results()

    print("Все данные успешно обработаны и сохранены.")

if __name__ == "__main__":
    main()
