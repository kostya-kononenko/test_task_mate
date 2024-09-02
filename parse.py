import csv
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


BASE_URL = "https://jobs.dou.ua/"
HOME_URL = urljoin(BASE_URL, "vacancies/?category=Front%20End")

NUM_VACANCIES = 50

VACANCIES_OUTPUT_CSV_PATH = "vacancies.csv"

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


@dataclass
class Vacancy:
    title: str
    description: str
    company: str
    city: list[str]
    publish_date: str


VACANCY_FIELDS = [field.name for field in fields(Vacancy)]


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = " ".join(line.strip() for line in text.splitlines() if line.strip())
    return text


def parse_single_vacancy(vacancy_soup: BeautifulSoup) -> Vacancy:

    return Vacancy(
        title=clean_text(vacancy_soup.select_one(".vt").text),
        description=clean_text(vacancy_soup.select_one(".sh-info").text),
        company=clean_text(vacancy_soup.select_one(".company").text),
        city=[cities.text for cities in vacancy_soup.select(".cities")],
        publish_date=clean_text(vacancy_soup.select_one(".date").text),
    )


def get_single_page_vacancies(page_soup: BeautifulSoup) -> [Vacancy]:
    vacancies = page_soup.select("li.l-vacancy")

    return [parse_single_vacancy(vacancy_soup) for vacancy_soup in vacancies]


def get_all_vacancies() -> [Vacancy]:
    all_vacancies = []

    while len(all_vacancies) < NUM_VACANCIES:
        page = _driver.page_source
        soup = BeautifulSoup(page, "html.parser")

        new_vacancies = get_single_page_vacancies(soup)
        all_vacancies.extend(new_vacancies)

        if len(all_vacancies) >= NUM_VACANCIES:
            break

        button = _driver.find_element(By.CLASS_NAME, "more-btn")
        button.click()

    return all_vacancies[:NUM_VACANCIES]


def write_vacancies_to_csv(vacancies: [Vacancy]) -> None:
    with open(
            VACANCIES_OUTPUT_CSV_PATH,
            "w",
            newline="",
            encoding="utf-8"
    ) as file:
        writer = csv.writer(file)
        writer.writerow(VACANCY_FIELDS)
        writer.writerows([astuple(vacancy) for vacancy in vacancies])


def main():
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        new_driver.get(HOME_URL)
        vacancies = get_all_vacancies()
        write_vacancies_to_csv(vacancies)


if __name__ == "__main__":
    main()
