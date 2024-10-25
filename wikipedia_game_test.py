import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

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


if __name__ == '__main__':
    unittest.main()
