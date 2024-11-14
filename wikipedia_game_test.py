from dataclasses import dataclass
from enum import Enum, auto

import unittest
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxWebdriver


class Browser(Enum):
    FIREFOX = auto()
    CHROME = auto()
    REMOTE = auto()

type WebDriver = ChromeWebdriver | FirefoxWebdriver

@dataclass
class LanguageDoesNotExist:
    start_article_title: str
    language: str

@dataclass
class StartNotAnArticle:
    start_article_title: str
    url: str

@dataclass
class TargetNotAnArticle:
    start_article_title: str
    target_article_title: str
    url: str

@dataclass
class GameError:
    start_article_title: str
    article_title: str

@dataclass
class CircleDetected:
    start_article_title: str
    target_article_title: str
    circle_article_title: str
    total_steps: int
    circle_steps: int

@dataclass
class TargetFound:
    start_article_title: str
    target_article_title: str
    total_steps: int

type GameResult = LanguageDoesNotExist | StartNotAnArticle | TargetNotAnArticle | CircleDetected | TargetFound | GameError


class WikipediaGame():
    def __init__(self, browser_type: Browser, headless: bool, grid_url: str):
        self.init_driver(browser_type, headless, grid_url)


    def init_driver(self, browser_type: Browser, headless: bool, grid_url: str) -> WebDriver:
        driver = None
        match browser_type:
            case Browser.FIREFOX:
                from selenium.webdriver.firefox.options import Options
                browser_options = Options()
                if headless:
                    browser_options.add_argument("--headless")
                driver = webdriver.Firefox(options=browser_options)
            case Browser.CHROME:
                from selenium.webdriver.chrome.options import Options
                browser_options = Options()
                if headless:
                    browser_options.add_argument("--headless")
                driver = webdriver.Chrome(options=browser_options)
            case Browser.REMOTE:
                from selenium.webdriver.chrome.options import Options
                browser_options = Options()
                if headless:
                    browser_options.add_argument("--headless")
                driver = webdriver.Remote(
                    command_executor=grid_url,
                    options=browser_options
                )

        self.driver = driver


    def check_if_language_exists(self, language: str) -> bool:
        url = f"https://{language}.wikipedia.org/"
        try:
            self.driver.get(url)
            return True
        except WebDriverException:
            return False


    def check_if_article_exists(self, url: str) -> bool:
        try:
            self.driver.get(url)
            _ = self.driver.find_element(By.CLASS_NAME, "noarticletext")
            return False
        except NoSuchElementException:
            return True


    def get_article_title(self) -> str:
        selectors = [
            (By.CLASS_NAME, "mw-page-title-main"),
            (By.CLASS_NAME, "mw-first-heading"),
        ]
        for by, value in selectors:
            try:
                element = self.driver.find_element(by, value)
                return element.text
            except Exception as _:
                continue

        print(f"No title found for the following article: {self.driver.current_url}")
        return None


    def get_brackets_depth_until(self, text: str, end_index: int) -> int:
        if len(text) < end_index:
            return -1

        depth = 0
        for char in text[:end_index]:
            match char:
                case '(' | '[':
                    depth += 1
                case ')' | ']':
                    depth -= 1
                case _:
                    pass

        return depth


    def get_first_link_url(self) -> str:
        content = self.driver.find_element(By.ID, "mw-content-text")
        main_content = content.find_element(By.CLASS_NAME, "mw-parser-output")

        paragraphs = main_content.find_elements(By.XPATH, "./p | ./ul | ./ol")
        for paragraph in paragraphs:
            links = paragraph.find_elements(By.XPATH,
                """
                .//a[
                    (
                        starts-with(@href, '/wiki/')
                        or
                        starts-with(@href, '#')
                    )
                    and
                    not(ancestor::table)
                    and
                    not(ancestor::figure)
                    and
                    not(ancestor::sup)
                    and
                    not(
                        contains(
                            substring-after(@href, '/wiki/'),
                            ':'
                        )
                    )
                ]
                """
            )

            for link in links:
                paragraph_html = paragraph.get_attribute('outerHTML')
                search_text = link.text + "<"
                end_index = paragraph_html.find(search_text)+len(search_text)
                brackets_depth = self.get_brackets_depth_until(paragraph_html, end_index)
                if brackets_depth==0:
                    return link.get_attribute("href")

        return None


    def run_game(
            self,
            start_aticle_title: str = "Special:Random",
            target_article_title: str = "Philosophy",
            language: str = "en"
    ) -> GameResult:
        if not self.check_if_language_exists(language):
            return LanguageDoesNotExist(start_aticle_title, language)

        base_url = f"https://{language}.wikipedia.org/wiki/"
        start_url = base_url+start_aticle_title.replace(" ", "_")
        if not self.check_if_article_exists(start_url):
            return StartNotAnArticle(start_aticle_title, start_url)

        target_url = base_url+target_article_title.replace(" ", "_")
        if not self.check_if_article_exists(target_url):
            return TargetNotAnArticle(target_article_title, target_url)

        print("Start URL:", start_url)

        steps: int = 0
        visited: dict[str, int] = {}
        try:
            self.driver.get(start_url)
            title = self.get_article_title()
            visited[title.lower()] = steps
            print(f"{steps:3} {title} ({self.driver.current_url})")

            while True:
                next_url = self.get_first_link_url()
                self.driver.get(next_url)
                title = self.get_article_title()
                title_lowercase = title.lower()

                steps += 1
                if title == target_article_title:
                    print(f"{steps:3} └─ {title} ({self.driver.current_url})")
                    print(f"Arrived at \"{title}\" after {steps} steps.\n")
                    return TargetFound(start_aticle_title, target_article_title, steps)
                elif title_lowercase in visited:
                    print(f"{steps:3} └─ {title} ({self.driver.current_url})")
                    print(f"Circle detected after {steps} steps.\n")
                    return CircleDetected(
                        start_aticle_title,
                        target_article_title,
                        title,
                        steps,
                        steps-visited[title_lowercase]
                    )
                else:
                    print(f"{steps:3} ├─ {title} ({self.driver.current_url})")
                    visited[title_lowercase] = steps
        except Exception as e:
            print("An error occurred:", e)
            return GameError(start_aticle_title)

    def __del__(self):
            self.driver.quit()


class WikipediaGameTest(unittest.TestCase):

    def setUp(self):
        """Set up the Selenium WebDriver (using remote Docker) before each test."""
        selenium_grid_url = "http://localhost:4444/wd/hub"
        self.driver = webdriver.Remote(
            command_executor=selenium_grid_url,
            options=webdriver.ChromeOptions()
        )
        self.start_url = "https://de.wikipedia.org/wiki/Spezial:Zufällige_Seite"
        self.target_word = "Philosophie"
        self.max_steps = 20
        self.visited_urls = []

    def tearDown(self):
        """Clean up resources after each test."""
        self.driver.quit()

    def test_find_philosophie(self):
        """Test to follow links and find the word 'Philosophie'."""
        driver = self.driver
        driver.get(self.start_url)

        steps = 0
        self.visited_urls.append(driver.current_url)

        while steps < self.max_steps:
            # Get the page's visible text content.
            body_text = driver.find_element(By.TAG_NAME, "body").text

            # Check if the target word is visible in the body text.
            if self.target_word in body_text:
                print(f"The word '{self.target_word}' was found on the page after {steps} steps!")
                self.assertIn(self.target_word, body_text)  # Ensure it is visible
                break

            content = driver.find_element(By.ID, "mw-content-text")
            paragraphs = content.find_elements(By.TAG_NAME, "p")

            found_link = False
            for paragraph in paragraphs:
                links = paragraph.find_elements(By.TAG_NAME, "a")
                for link in links:
                    href = link.get_attribute("href")

                    # Check if link has valid href.
                    if href:
                        # Check the computed CSS style for `font-style`
                        font_style = link.value_of_css_property("font-style")

                        if font_style != "italic":  # Only proceed if the text is not italicized.
                            found_link = True
                            self.visited_urls.append(href)
                            driver.get(href)
                            steps += 1
                            break
                if found_link:
                    break

            # Wait briefly to simulate user interaction and reduce server load.
            time.sleep(0.5)
        else:
            print(f"Maximum steps reached; the word '{self.target_word}' was not found.")
            self.fail(f"The word '{self.target_word}' was not found after {self.max_steps} steps.")

        print("Visited pages:")
        for url in self.visited_urls:
            print(url)


def run_game():
    rounds_arguments = []
    with open("./input.txt", "r", encoding="utf-8") as file:
        for line in file.readlines():
            if line.startswith("#"):
                continue

            start = None
            target = None
            language = None
            arguments: list[str] = [argument.strip() for argument in line.split("|")]
            if len(arguments)==0:
                continue
            if len(arguments)>0:
                start = arguments[0]
            if len(arguments)>1:
                target = arguments[1]
            if len(arguments)>2:
                language = arguments[2]

            rounds_arguments.append((start, target, language))

    game = WikipediaGame(Browser.REMOTE, True, "http://localhost:4444/wd/hub")
    # game = WikipediaGame(Browser.FIREFOX, True, None)

    rounds: list[GameResult] = []
    for start, target, language in rounds_arguments:
        if language!=None:
            rounds.append(game.run_game(start, target, language))
        elif target!=None:
            rounds.append(game.run_game(start, target))
        else:
            rounds.append(game.run_game(start))

    with open("./output.txt", "w", encoding="utf-8") as file:
        for game_result in rounds:
            file.write(f"{game_result.start_article_title}:\n")
            match game_result:
                case LanguageDoesNotExist():
                    file.write(f"\tNo wikipedia site for the language \"{game_result.language}\" found.\n\n")
                case StartNotAnArticle():
                    file.write(f"\tNo wikipedia article found for the start \"{game_result.start_article_title}\" (url: {game_result.url}).\n\n")
                case TargetNotAnArticle():
                    file.write(f"\tNo wikipedia article found for the target \"{game_result.target_article_title}\"  (url: {game_result.url}).\n\n")
                case GameError():
                    file.write(f"\tAn error occurred while playing from \"{game_result.start_article_title}\".\n\n")
                case CircleDetected():
                    file.write(f"\tA circle was detected after starting from \"{game_result.start_article_title}\".\n")
                    file.write(f"\tThe circle started at \"{game_result.circle_article_title}\" and is {game_result.circle_steps} steps long.\n\n")
                case TargetFound():
                    file.write(f"\tArrived at \"{game_result.target_article_title}\" from \"{game_result.start_article_title}\" after {game_result.total_steps} steps.\n\n")


if __name__ == '__main__':
    run_game()
    # unittest.main()
