import pandas as pd
import sys
import os

results = []

RESULTS_FILE = 'files/описание_шин.xlsx'

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