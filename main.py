import os
import requests
from dotenv import load_dotenv
import time
from terminaltables import SingleTable

load_dotenv()
SUPERJOB_API_KEY = os.getenv("API_SUPERJOB_KEY")
SUPERJOB_URL = "https://api.superjob.ru/2.0/vacancies/"

LANGUAGE_ALIASES = {
    "Go": ["Go", "Golang"],
    "JavaScript": ["JavaScript", "JS", "Node"],
    "C#": ["C#", ".NET", "CSharp"],
    "Java": ["Java"],
    "Python": ["Python"],
    "1C": ["1C", "1С", "1C:Enterprise"],
}

RUB_CODES = {"RUR", "RUB", "rub", "Rub", "rur"}

def predict_rub_salary(salary_min, salary_max, currency=None):
    if currency and currency not in RUB_CODES:
        return None
    if not salary_min and not salary_max:
        return None
    if salary_min and salary_max:
        return (salary_min + salary_max) / 2
    if salary_min:
        return salary_min * 1.2
    if salary_max:
        return salary_max * 0.8


def get_hh_vacancies(search_query, region_id=1, vacancies_per_page=100, page=0):
    params = {"text": search_query, "area": region_id, "per_page": vacancies_per_page, "page": page}
    resp = requests.get("https://api.hh.ru/vacancies", params=params)
    resp.raise_for_status()
    return resp.json()

def get_all_hh_vacancies(search_query, region_id=1, vacancies_per_page=100):
    page = 0
    all_vacancies = []
    total_found = 0
    while True:
        hh_page_response = get_hh_vacancies(search_query, region_id=region_id, vacancies_per_page=vacancies_per_page, page=page)
        if page == 0:
            total_found = hh_page_response.get("found", 0)
        page_vacancies = hh_page_response.get("items", [])
        all_vacancies.extend(page_vacancies)
        pages_total = hh_page_response.get("pages")
        if not pages_total or page >= pages_total - 1:
            break
        time.sleep(0.15)
        page += 1
    return total_found, all_vacancies

def get_all_hh_vacancies_multi(queries, region_id=1, vacancies_per_page=100):
    unique_vacancies = []
    seen_ids = set()
    total_found_sum = 0
    for search_query in queries:
        found_count, vacancies = get_all_hh_vacancies(search_query, region_id=region_id, vacancies_per_page=vacancies_per_page)
        total_found_sum += found_count
        for vacancy in vacancies:
            vacancy_id = vacancy.get("id")
            if vacancy_id not in seen_ids:
                seen_ids.add(vacancy_id)
                unique_vacancies.append(vacancy)
    return total_found_sum, unique_vacancies

def get_hh_statistics(languages):
    statistics = {}
    for language in languages:
        queries = LANGUAGE_ALIASES.get(language, [language])
        total_found, vacancy_list = get_all_hh_vacancies_multi(queries)
        total_salary_sum, processed_vacancies_count = 0, 0
        for vacancy in vacancy_list:
            salary_details = vacancy.get("salary")
            if not salary_details:
                continue
            predicted_salary = predict_rub_salary(
                salary_details.get("from"),
                salary_details.get("to"),
                salary_details.get("currency")
            )
            if predicted_salary:
                total_salary_sum += predicted_salary
                processed_vacancies_count += 1
        avg_salary = int(total_salary_sum / processed_vacancies_count) if processed_vacancies_count else 0
        statistics[language] = {
            "vacancies_found": total_found,
            "vacancies_processed": processed_vacancies_count,
            "average_salary": avg_salary
        }
    return statistics


def get_superjob_vacancies(search_query, town_id=4, vacancies_count=100, page=0):
    headers = {"X-Api-App-Id": SUPERJOB_API_KEY, "User-Agent": "Mozilla/5.0"}
    params = {"keyword": search_query, "town": town_id, "count": vacancies_count, "page": page}
    resp = requests.get(SUPERJOB_URL, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()

def get_all_superjob_vacancies(search_query, town_id=4, vacancies_count=100):
    page = 0
    all_objects = []
    total_found = 0
    while True:
        page_data = get_superjob_vacancies(search_query, town_id=town_id, vacancies_count=vacancies_count, page=page)
        if page == 0:
            total_found = page_data.get("total", 0)
        objects = page_data.get("objects", [])
        all_objects.extend(objects)
        more = page_data.get("more")
        if not more:
            break
        time.sleep(0.15)
        page += 1
    return {"total": total_found, "objects": all_objects}

def get_all_superjob_vacancies_multi(queries, town_id=4, vacancies_count=100):
    merged_vacancies = []
    seen_ids = set()
    total_found_sum = 0
    for search_query in queries:
        superjob_page_result = get_all_superjob_vacancies(search_query, town_id=town_id, vacancies_count=vacancies_count)
        total_found_sum += superjob_page_result.get("total", 0)
        for vacancy in superjob_page_result.get("objects", []):
            vacancy_id = vacancy.get("id")
            if vacancy_id not in seen_ids:
                seen_ids.add(vacancy_id)
                merged_vacancies.append(vacancy)
    return {"total": total_found_sum, "objects": merged_vacancies}

def get_superjob_statistics(languages):
    stats = {}
    for language in languages:
        queries = LANGUAGE_ALIASES.get(language, [language])
        vacancies_data = get_all_superjob_vacancies_multi(queries)
        total_found = vacancies_data.get("total", 0)
        vacancies = vacancies_data.get("objects", [])
        total_salary_sum, processed_vacancies_count = 0, 0
        for vacancy in vacancies:
            predicted_salary = predict_rub_salary(
                vacancy.get("payment_from"),
                vacancy.get("payment_to"),
                vacancy.get("currency")
            )
            if predicted_salary:
                total_salary_sum += predicted_salary
                processed_vacancies_count += 1
        avg_salary = int(total_salary_sum / processed_vacancies_count) if processed_vacancies_count else 0
        stats[language] = {
            "vacancies_found": total_found,
            "vacancies_processed": processed_vacancies_count,
            "average_salary": avg_salary
        }
    return stats


def print_statistics_table(statistics_data, title="Job Stats"):
    headers = [
        "Язык программирования",
        "Найдено вакансий",
        "Обработано вакансий",
        "Средняя зарплата"
    ]
    table_rows = [headers]
    for language, language_stats in statistics_data.items():
        table_rows.append(
            [
                language,
                language_stats["vacancies_found"],
                language_stats["vacancies_processed"],
                language_stats["average_salary"],
            ]
        )
    table = SingleTable(table_rows, title)
    print(table.table)

def main():
    programming_languages = ["Python", "Java", "C#", "Go", "JavaScript", "1C"]
    hh_statistics = get_hh_statistics(programming_languages)
    print_statistics_table(hh_statistics, title="HeadHunter Moscow")
    sj_statistics = get_superjob_statistics(programming_languages)
    print_statistics_table(
        sj_statistics,
        title="SuperJob Moscow"
    )


if __name__ == "__main__":
    
    main()
