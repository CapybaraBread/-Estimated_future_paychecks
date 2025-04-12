import os
import requests
from dotenv import load_dotenv


def get_hh_vacancies(keyword, area=1, per_page=100):
    params = {"text": keyword, "area": area, "per_page": per_page}
    resp = requests.get("https://api.hh.ru/vacancies", params=params)
    resp.raise_for_status()
    return resp.json()


def predict_rub_salary_for_hh(vacancy):
    salary_data = vacancy.get("salary")
    if not salary_data or salary_data.get("currency") != "RUR":
        return None
    salary_from = salary_data.get("from")
    salary_to = salary_data.get("to")
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    if salary_from:
        return salary_from * 1.2
    if salary_to:
        return salary_to * 0.8
    return None


def get_hh_statistics(languages):
    statistics = {}
    for language in languages:
        data = get_hh_vacancies(language)
        found = data.get("found", 0)
        vacancies = data.get("items", [])
        total_salary, processed_count = 0, 0
        for vacancy in vacancies:
            predicted_salary = predict_rub_salary_for_hh(vacancy)
            if predicted_salary:
                total_salary += predicted_salary
                processed_count += 1
        average_salary = int(total_salary / processed_count) if processed_count else 0
        statistics[language] = {
            "vacancies_found": found,
            "vacancies_processed": processed_count,
            "average_salary": average_salary
        }
    return statistics


def predict_rub_salary_for_superJob(vacancy):
    payment_from = vacancy.get("payment_from")
    payment_to = vacancy.get("payment_to")
    if not payment_from and not payment_to:
        return None
    if payment_from and payment_to:
        return (payment_from + payment_to) / 2
    if payment_from:
        return payment_from * 1.2
    if payment_to:
        return payment_to * 0.8


def get_superjob_vacancies(keyword, town=4, count=100):
    headers = {"X-Api-App-Id": SUPERJOB_API_KEY, "User-Agent": "Mozilla/5.0"}
    params = {"keyword": keyword, "town": town, "count": count}
    resp = requests.get(SUPERJOB_URL, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


def get_superjob_statistics(languages):
    stats = {}
    for language in languages:
        data = get_superjob_vacancies(language)
        found = data.get("total", 0)
        vacancies = data.get("objects", [])
        total_salary, processed_count = 0, 0
        for vacancy in vacancies:
            predicted_salary = predict_rub_salary_for_superJob(vacancy)
            if predicted_salary:
                total_salary += predicted_salary
                processed_count += 1
        average_salary = int(total_salary / processed_count) if processed_count else 0
        stats[language] = {
            "vacancies_found": found,
            "vacancies_processed": processed_count,
            "average_salary": average_salary
        }
    return stats


def print_statistics_table(stats, title="Job Stats"):
    headers = [
        "Язык программирования",
        "Найдено вакансий",
        "Обработано вакансий",
        "Средняя зарплата"
    ]
    rows = [headers]
    for language, language_stats in stats.items():
        rows.append(
            [
                language,
                language_stats["vacancies_found"],
                language_stats["vacancies_processed"],
                language_stats["average_salary"],
            ]
        )
    col_widths = [max(len(str(cell)) for cell in col) for col in zip(*rows)]
    separator_inner = '+'.join('-' * (w + 2) for w in col_widths)
    sep = f"+{separator_inner}+"
    print(f"\n{title}\n{sep}")
    for index, table_row in enumerate(rows):
        row_str = ' | '.join(str(cell).ljust(col_widths[j]) for j, cell in enumerate(table_row))
        print(f"| {row_str} |")
        print(sep)


def main():
    global SUPERJOB_API_KEY, SUPERJOB_URL
    load_dotenv()
    SUPERJOB_API_KEY = os.getenv("API_SUPERJOB_KEY")
    SUPERJOB_URL = "https://api.superjob.ru/2.0/vacancies/"
    langs = ["Python", "Java", "C#", "Go", "JavaScript", "1C"]
    hh_stats = get_hh_statistics(langs)
    print_statistics_table(hh_stats, title="HeadHunter Moscow")
    sj_stats = get_superjob_statistics(langs)
    print_statistics_table(
        sj_stats,
        title="SuperJob Moscow"
    )


if __name__ == "__main__":

    main()
