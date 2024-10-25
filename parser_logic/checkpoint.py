import pandas as pd
import sys
import os

results = []

RESULTS_FILE = 'files/описание_шин.xlsx'

def signal_handler(app_instance, sig, frame):
    message = "\nПолучен сигнал для завершения. Сохранение промежуточных результатов..."
    print(message)
    app_instance.log_queue.put((message, "DarkOrange", 'bold'))
    save_results(app_instance.log_queue)
    sys.exit(0)

def save_results(results, log_queue):
    try:
        if results:
            results_df = pd.DataFrame(results)
            results_df.to_excel(RESULTS_FILE, index=False)
            message = f"Промежуточные результаты успешно сохранены в {RESULTS_FILE}"
            print(message)
            log_queue.put((message, "LimeGreen", 'bold'))
    except Exception as e:
        error_message = f"Ошибка при сохранении результатов: {e}"
        print(error_message)
        log_queue.put(error_message, "Red", 'bold')

def load_previous_results(log_queue):
    if os.path.exists(RESULTS_FILE):
        message = f"Загрузка предыдущих результатов из {RESULTS_FILE}\n"
        print(message)
        log_queue.put((message, "LimeGreen", 'Bold'))
        return pd.read_excel(RESULTS_FILE).to_dict(orient='records')
    return []