import os
from dotenv import load_dotenv
import requests

load_dotenv()

SUPERJOB_API_KEY = os.getenv("API_SUPERJOB_KEY")
SUPERJOB_URL = "https://api.superjob.ru/2.0/vacancies/"


# HH.ru


def get_hh_vacancies(keyword, area=1, per_page=100):
    params = {"text": keyword, "area": area, "per_page": per_page}
    resp = requests.get("https://api.hh.ru/vacancies", params=params)
    resp.raise_for_status()
    return resp.json()


def predict_rub_salary_for_hh(vac):
    sal = vac.get("salary")
    if not sal or sal.get("currency") != "RUR":
        return None
    frm = sal.get("from")
    to = sal.get("to")
    if frm and to:
        return (frm + to) / 2
    if frm:
        return frm * 1.2
    if to:
        return to * 0.8
    return None


def get_hh_statistics(langs):
    stats = {}
    for lang in langs:
        data = get_hh_vacancies(lang)
        found = data.get("found", 0)
        items = data.get("items", [])
        total, cnt = 0, 0
        for item in items:
            s = predict_rub_salary_for_hh(item)
            if s is not None:
                total += s
                cnt += 1
        avg = int(total / cnt) if cnt else 0
        stats[lang] = {
            "vacancies_found": found,
            "vacancies_processed": cnt,
            "average_salary": avg
        }
    return stats


# SuperJob


def predict_rub_salary_for_superJob(vac):
    pf = vac.get("payment_from")
    pt = vac.get("payment_to")
    if pf is None and pt is None:
        return None
    if pf is not None and pt is not None:
        return (pf + pt) / 2
    if pf is not None:
        return pf * 1.2
    if pt is not None:
        return pt * 0.8


def get_superjob_vacancies(keyword, town=4, count=100):
    headers = {"X-Api-App-Id": SUPERJOB_API_KEY, "User-Agent": "Mozilla/5.0"}
    params = {"keyword": keyword, "town": town, "count": count}
    resp = requests.get(SUPERJOB_URL, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


def get_superjob_statistics(langs):
    stats = {}
    for lang in langs:
        data = get_superjob_vacancies(lang)
        found = data.get("total", 0)
        vacs = data.get("objects", [])
        total, cnt = 0, 0
        for vac in vacs:
            s = predict_rub_salary_for_superJob(vac)
            if s is not None:
                total += s
                cnt += 1
        avg = int(total / cnt) if cnt else 0
        stats[lang] = {
            "vacancies_found": found,
            "vacancies_processed": cnt,
            "average_salary": avg
        }
    return stats


# Вывод таблицы


def print_statistics_table(stats, title="Job Stats"):
    headers = [
        "Язык программирования",
        "Найдено вакансий",
        "Обработано вакансий",
        "Средняя зарплата"
    ]
    rows = [headers]
    for lang, data in stats.items():
        rows.append([
            lang,
            data["vacancies_found"],
            data["vacancies_processed"],
            data["average_salary"]
            ])
    col_widths = [max(len(str(cell)) for cell in col) for col in zip(*rows)]
    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    print(f"\n{title}\n" + sep)
    for i, row in enumerate(rows):
        print("| " + " | ".join(str(cell).ljust(col_widths[j]) for j, cell in enumerate(row)) + " |")
        print(sep)


if __name__ == "__main__":
    langs = ["Python", "Java", "C#", "Go", "JavaScript", "1C"]
    hh_stats = get_hh_statistics(langs)
    print_statistics_table(hh_stats, title="HeadHunter Moscow")
    sj_stats = get_superjob_statistics(langs)
    print_statistics_table(sj_stats, title="SuperJob Moscow")
