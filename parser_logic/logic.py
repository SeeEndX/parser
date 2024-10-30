import requests
from bs4 import BeautifulSoup
import random
import re
import xml.etree.ElementTree as ET
from .checkpoint import *

def load_proxies(file_path):
    with open(file_path, 'r') as f:
        proxies = [line.strip() for line in f.readlines()]
    return proxies

def get_random_proxy(proxies):
    proxy = random.choice(proxies)
    ip, port, user, password = proxy.split(':')
    return {
        'http': f'http://{user}:{password}@{ip}:{port}',
        'https': f'http://{user}:{password}@{ip}:{port}'
    }

def parse_with_requests(url, proxies, app_instance):
    proxy = get_random_proxy(proxies)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0"
    }
    message = f"\nПарсинг сайта: {url} с прокси: {proxy}\n"
    print(message)
    app_instance.log_queue.put((message, "Black", 'normal'))

    try:
        response = requests.get(url, headers=headers, proxies=proxy, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        return f"Ошибка при парсинге: {e}"

def clean_text(text):
    return re.sub(r'[^\w\s]', '', text.lower()).strip()

def split_model(model):
    return clean_text(model).split()

def find_best_match(model, tyre_items, app_instance):
    model_words = split_model(model)
    best_match = None
    highest_count = 0

    for item in tyre_items:
        link = item.find('a', class_='b-link')
        if link:
            tyre_name = clean_text(link.get_text(strip=True))
            tyre_words = split_model(tyre_name)

            matches = sum(1 for word in model_words if word in tyre_words)

            if matches > highest_count:
                highest_count = matches
                best_match = link['href']
                message =f"Найдена модель: {tyre_name} с {matches} совпадениями."
                print(message)
                app_instance.log_queue.put((message, "LimeGreen", 'normal'))

    return best_match if highest_count >= 1 else None

def get_full_description_drom(soup):
    description_div = soup.find('div', class_='b-media-cont', itemprop='reviewBody')
    
    if not description_div:
        return 'Описание не найдено для модели'
    
    description_text = description_div.get_text(strip=True)
    
    hidden_text_span = description_div.find('span', class_='js-noscript-show')
    if hidden_text_span:
        hidden_text = hidden_text_span.get_text(strip=True)
        description_text += ' ' + hidden_text
    
    return description_text

def get_tyre_description_drom(brand, model, proxies, app_instance):
    if not model:
        return "Обнаружено отсутствие модели"

    brand_lower = brand.lower()
    search_url = f'https://www.drom.ru/shina/{brand_lower}/'
    soup = parse_with_requests(search_url, proxies, app_instance)

    if isinstance(soup, str):
        print(soup)
        return soup

    tyre_items = soup.find_all('div', class_='b-selectCars__item')
    model_url = find_best_match(model, tyre_items, app_instance)

    if model_url:
        model_description_soup = parse_with_requests(model_url, proxies, app_instance)
        if isinstance(model_description_soup, str):
            print(model_description_soup)
            return model_description_soup

        full_description = get_full_description_drom(model_description_soup)
        return full_description
    else:
        return 'Модель не найдена'

def find_best_match_mosautoshina(model, tyre_items, app_instance):
    model_words = split_model(model)
    best_match = None
    highest_count = 0

    for item in tyre_items:
        tyre_name = clean_text(item.select_one('div.product-name.model-name').get_text(strip=True))
        tyre_words = split_model(tyre_name)

        matches = sum(1 for word in model_words if word in tyre_words)

        if matches > highest_count:
            highest_count = matches
            link = item.find('a', class_='product-container')
            if link and 'href' in link.attrs:
                best_match = 'https://mosautoshina.ru' + link['href']
                message = f"Найдена модель: {tyre_name} с {matches} совпадениями."
                print(message)
                app_instance.log_queue.put((message, "LimeGreen", 'normal'))

    return best_match if highest_count >= 1 else None

def get_full_description_mosautoshina(soup, model):
    description_div = soup.find('div', class_='full-description')
    
    if not description_div:
        return 'Описание не найдено для модели'
    
    description_text = description_div.get_text(strip=True)
    
    description_text = description_text.replace("Показать всё описание", "").strip()
    description_text = re.sub(r'(?i)^(Описание)(?!\s)', r'\1 ', description_text)
    model_pattern = re.escape(model)
    description_text = re.sub(r'(?i)(' + model_pattern + r')(?!\s)', r'\1 ', description_text)
    
    return description_text

def get_tyre_description_mosautoshina(brand, model, proxies, app_instance):
    if not model:
        return "Обнаружено отсутствие модели"

    brand_lower = brand.lower()
    search_url = f'https://mosautoshina.ru/catalog/tyre/{brand_lower}/'
    soup = parse_with_requests(search_url, proxies, app_instance)

    if isinstance(soup, str):
        print(soup)
        return soup

    tyre_items = soup.select('li.product.model')
    model_url = find_best_match_mosautoshina(model, tyre_items, app_instance)

    if model_url:
        model_description_soup = parse_with_requests(model_url, proxies, app_instance)
        if isinstance(model_description_soup, str):
            print(model_description_soup)
            return model_description_soup

        full_description = get_full_description_mosautoshina(model_description_soup, model)
        return full_description
    else:
        return 'Модель не найдена'
    
def get_full_description_autoshini(soup, model):
    description_div = soup.find('div', class_='tab prodinfo lineheight visible')
    
    if not description_div:
        return 'Описание не найдено для модели'
    
    description_text = description_div.get_text(strip=True, separator='\n')

    unwanted_start = description_text.find('Информация о ')
    
    if unwanted_start != -1:
        description_text = description_text[:unwanted_start].strip()

    return description_text if description_text else 'Описание не найдено для модели'

def find_best_match_autoshini(model, tyre_items, app_instance):
    model_words = split_model(model)
    best_match = None
    highest_count = 0

    for item in tyre_items:
        tyre_name_element = item.find('a', class_='snapshot-catname')
        if tyre_name_element:
            tyre_name = clean_text(tyre_name_element.get_text(strip=True))
            tyre_words = split_model(tyre_name)

            matches = sum(1 for word in model_words if word in tyre_words)

            if matches > highest_count:
                highest_count = matches
                link = tyre_name_element
                if link and 'href' in link.attrs:
                    best_match = 'https://autoshini.ru' + link['href']
                    message = f"Найдена модель: {tyre_name} с {matches} совпадениями."
                    print(message)
                    app_instance.log_queue.put((message, "LimeGreen", 'normal'))

    return best_match if highest_count >= 1 else None


def get_tyre_description_autoshini(brand, model, proxies, app_instance):
    if not model:
        return {"description": "Обнаружено отсутствие модели"}

    brand_lower = brand.lower()
    search_url = f'https://autoshini.ru/shop/shiny-{brand_lower}/'
    soup = parse_with_requests(search_url, proxies, app_instance)

    if isinstance(soup, str):
        print(soup)
        return {"description": soup}

    tyre_items = soup.find_all('div', class_='snapshot-item')
    model_url = find_best_match_autoshini(model, tyre_items, app_instance)

    if model_url:
        model_description_soup = parse_with_requests(model_url, proxies, app_instance)
        if isinstance(model_description_soup, str):
            print(model_description_soup)
            return {"description": model_description_soup}

        full_description = get_full_description_autoshini(model_description_soup, model)
        return {
            'model_name': model,
            'description': full_description
        }
    else:
        return {"description": 'Модель не найдена'}

def get_full_description_4tochki(soup):
    description_div = soup.find('div', class_='product-description')
    
    if not description_div:
        return 'Описание не найдено для модели'
    
    description_text = description_div.get_text(strip=True, separator='\n')
    return description_text if description_text else 'Описание не найдено для модели'


def find_best_match_4tochki(model, tyre_items, app_instance):
    model_words = split_model(model)
    best_match = None
    highest_count = 0

    for item in tyre_items:
        tyre_name_element = item.find('a', class_='d-flex align-items-center mt-2')
        if tyre_name_element:
            tyre_name = clean_text(tyre_name_element.get_text(strip=True))

            brand_element = item.find(itemprop="brand")
            brand_name = brand_element.find('meta', itemprop="name")['content'] if brand_element else ""

            full_tyre_name = f"{brand_name} {tyre_name}".strip() if brand_name else tyre_name
            tyre_words = split_model(full_tyre_name)

            matches = sum(1 for word in model_words if word in tyre_words)

            if matches > highest_count:
                highest_count = matches
                if 'href' in tyre_name_element.attrs:
                    best_match = 'https://www.4tochki.ru' + tyre_name_element['href']
                    message = f"Найдена модель: {full_tyre_name} с {matches} совпадениями."
                    print(message)
                    app_instance.log_queue.put((message, "LimeGreen", 'normal'))

    return best_match if highest_count >= 1 else None



def get_tyre_description_4tochki(brand, model, proxies, app_instance):
    if not model:
        return {"description": "Обнаружено отсутствие модели"}

    brand_lower = brand.lower()
    brand_url = f'https://4tochki.ru/catalog/tyres/{brand_lower}/'
    soup = parse_with_requests(brand_url, proxies, app_instance)

    if isinstance(soup, str):
        print(soup)
        return {"description": soup}

    tyre_items = soup.find_all('div', class_='product-item')
    model_url = find_best_match_4tochki(model, tyre_items, app_instance)

    if model_url:
        model_description_soup = parse_with_requests(model_url, proxies, app_instance)
        if isinstance(model_description_soup, str):
            print(model_description_soup)
            return {"description": model_description_soup}

        full_description = get_full_description_4tochki(model_description_soup)
        return {
            'model_name': model,
            'description': full_description
        }
    else:
        return {"description": 'Модель не найдена'}

def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    tires = []
    
    for tire in root.find('tires'):
        brand = tire.get('brand')
        product = tire.get('product')
        tires.append({'brand': brand, 'product': product})
    
    return tires

def already_processed(brand, model, previous_results):
    for result in previous_results:
        if result['Название шины'] == f"{brand} {model}":
            return True
    return False

def processing(log_queue, app_instance, selected_sites):
    log_queue.put(("Процесс парсинга начался...\n", "Green", 'bold'))
    previous_results = load_previous_results(log_queue)
    global results

    if previous_results:
        results = previous_results
    
    tires = parse_xml('files/tires.xml')
    proxies = load_proxies('files/proxies.txt')

    description_drom = None

    for tire in tires:
        if not app_instance.is_running:
            message="Обработка остановлена."
            log_queue.put((message, "DarkOrange", 'normal'))
            message = "\nВсе данные успешно обработаны и сохранены.\n_______________________________________________________________________\n"
            log_queue.put((message, "LimeGreen", 'normal'))
            break
        
        brand_full = tire['brand']
        model = tire['product']

        brand = brand_full.split()[0] if brand_full else "Unknown"

        if not model:
            message = f"Обнаружено отсутствие модели для бренда: {brand}"
            log_queue.put((message, "DarkOrange", 'normal'))
            continue

        if already_processed(brand, model, previous_results):
            message = f"Шина {brand} {model} уже обработана, пропускаем..."
            log_queue.put((message, "DarkOrange", 'normal'))
            continue

        description_drom = ''
        description_mosautoshina = ''
        description_autoshini = ''
        description_4tochki = ''

        if "Дром" in selected_sites:
            description_drom = get_tyre_description_drom(brand, model, proxies, app_instance)
            message = f"Описание с drom.ru для {brand} {model}: {description_drom}"
            log_queue.put((message, "Black", 'normal'))
        
        if "Мосавтошина" in selected_sites:
            description_mosautoshina = get_tyre_description_mosautoshina(brand, model, proxies, app_instance)
            message = f"Описание с mosautoshina.ru для {brand} {model}: {description_mosautoshina}"
            log_queue.put((message, "Black", 'normal'))

        if "Автошины" in selected_sites:
            description_autoshini = get_tyre_description_autoshini(brand, model, proxies, app_instance)
            message = f"Описание с autoshini.ru для {brand} {model}: {description_autoshini['description']}"
            log_queue.put((message, "Black", 'normal'))

        if "4 точки" in selected_sites:
            description_4tochki = get_tyre_description_4tochki(brand, model, proxies, app_instance)

            if isinstance(description_4tochki, str):
                message = f"Описание с 4tochki.ru для {brand} {model}: {description_4tochki}"
            else:
                message = f"Не удалось получить описание с 4tochki.ru для {brand} {model}: {description_4tochki}"
            
            log_queue.put((message, "Black", 'normal'))

        results.append({
            'Название шины': f"{brand} {model}",
            'Описание drom.ru': description_drom,
            'Описание mosautoshina.ru': description_mosautoshina,
            'Описание autoshini.ru': description_autoshini['description'] if isinstance(description_autoshini, dict) else description_autoshini,
            'Описание 4tochki.ru': description_4tochki
        })
        
        save_results(results, log_queue)
        
        if not app_instance.is_running.is_set(): 
            log_queue.put(("Обработка остановлена.\n", "DarkOrange", 'normal'))
            message = "\nВсе данные успешно обработаны и сохранены.\n_______________________________________________________________________\n"
            log_queue.put((message, "LimeGreen", 'normal'))
            break