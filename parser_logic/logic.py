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
    message = f"\n\nПарсинг сайта: {url} с прокси: {proxy}"
    print(message)
    app_instance.log_queue.put(message)

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
                app_instance.log_queue.put(message)

    return best_match if highest_count >= 1 else None

def get_full_description(soup):
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

        full_description = get_full_description(model_description_soup)
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
                app_instance.log_queue.put(message)

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

def processing(log_queue, app_instance):
    log_queue.put("Процесс парсинга начался...\n")
    previous_results = load_previous_results(log_queue)
    if previous_results:
        global results
        results = previous_results
    
    tires = parse_xml('files/tires.xml')
    proxies = load_proxies('files/proxies.txt')

    for tire in tires:
        if not app_instance.is_running:
            log_queue.put("Обработка остановлена.")
            break
        brand = tire['brand']
        model = tire['product']

        if not model:
            message = f"Обнаружено отсутствие модели для бренда: {brand}"
            print(message)
            log_queue.put(message)
            continue

        if already_processed(brand, model, previous_results):
            message = f"Шина {brand} {model} уже обработана, пропускаем..."
            print(message)
            log_queue.put(message)
            continue

        description_drom = get_tyre_description_drom(brand, model, proxies, app_instance)
        message = f"Описание с drom.ru для {brand} {model}: {description_drom}"
        print(message)
        log_queue.put(message)
        
        results.append({
            'Название шины': f"{brand} {model}",
            'Описание drom.ru': description_drom,
            'Описание mosautoshina.ru': ''
        })
        save_results(results, log_queue)

        description_mosautoshina = get_tyre_description_mosautoshina(brand, model, proxies, app_instance)
        message = f"Описание с mosautoshina.ru для {brand} {model}: {description_mosautoshina}"
        print(message)
        log_queue.put(message)

        for result in results:
            if result['Название шины'] == f"{brand} {model}":
                result['Описание mosautoshina.ru'] = description_mosautoshina

        save_results(results, log_queue)

    print("Все данные успешно обработаны и сохранены.")