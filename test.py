from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Set up remote connection to Selenium server in Docker
selenium_grid_url = "http://localhost:4444/wd/hub"

driver = webdriver.Remote(
    command_executor=selenium_grid_url,
    options=webdriver.ChromeOptions()
)

# The starting page on Wikipedia (replace this with any page)
start_url = "https://de.wikipedia.org/wiki/Spezial:Zufällige_Seite"
driver.get(start_url)

# Define rules
max_steps = 100  # Maximum steps to follow links
target_word = "Philosophie"  # Target word to find

# Step counter and visited URLs list
steps = 0
visited_urls = []

try:
    visited_urls.append(driver.current_url)
    while steps < max_steps:
        # Check if target word "Philosophie" is visible on the current page
        if target_word in driver.page_source:
            print(f"The word '{target_word}' was found on the page after {steps} steps!")
            break

        # Get the first valid link
        content = driver.find_element(By.ID, "mw-content-text")
        paragraphs = content.find_elements(By.TAG_NAME, "p")
        
        found_link = False
        for paragraph in paragraphs:
            links = paragraph.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href")

                # Check if link has valid href and is not in brackets
                if href and "(#" not in href:
                    # Check the computed CSS style for `font-style`
                    font_style = link.value_of_css_property("font-style")
                    
                    if font_style != "italic":  # Only proceed if the text is not italicized
                        found_link = True
                        visited_urls.append(href)
                        driver.get(href)
                        steps += 1
                        break
            if found_link:
                break

        # Wait briefly to simulate user interaction and reduce server load
        time.sleep(1)

    else:
        print("Maximum steps reached; the word 'Philosophie' was not found.")

finally:
    driver.quit()

# Output visited URLs
print("Visited pages:")
for url in visited_urls:
    print(url)
