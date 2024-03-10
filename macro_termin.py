"""
Huijo Kim (ccomkhj@gmail.com)
"""

import logging
import time
import requests
import yaml
import sys

from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

import pygame


# Load config
def load_config(file_path="data/config.yaml"):
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


config = load_config()
form_selections = config["form_selections"]
click_labels = config["click_labels"]

logging.basicConfig(
    format="%(asctime)s\t%(levelname)s\t%(message)s", level=logging.INFO
)


class WebDriver:
    def __init__(self, mode="local", implicit_wait_time=20):
        self.implicit_wait_time = implicit_wait_time
        self.mode = mode

    def __enter__(self):
        logging.info("Open browser")
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        if self.mode == "local":
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), options=options
            )
        else:
            self.driver = webdriver.Remote(
                command_executor="http://localhost:4444/wd/hub", options=options
            )
        self.driver.implicitly_wait(self.implicit_wait_time)
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        return self.driver

    def __exit__(self, exc_type, exc_value, exc_tb):
        logging.info("Close browser")
        self.driver.quit()


class MacroTermin:
    def __init__(self, mode):
        self.wait_time = config["termin_bot"]["wait_time"]
        self.sound_file = config["termin_bot"]["sound_file"]
        self.error_message = config["termin_bot"]["error_message"]
        self.slack_webhook_url = config.get("slack_webhook_url")

        if mode in ["local", "remote"]:
            self.mode = mode
        else:
            logging.error(
                f"Incorrect mode. Please select local or remote. current mode: {mode}"
            )
            raise ValueError

    def enter_start_page(self, driver):
        logging.info("Visit start page")
        driver.get("https://otv.verwalt-berlin.de/ams/TerminBuchen")
        driver.find_element(
            By.XPATH,
            '//*[@id="mainForm"]/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/a',
        ).click()
        time.sleep(5)

    def tick_off_agreement(self, driver: webdriver.Chrome):
        logging.info("Ticking off agreement")
        driver.find_element(By.XPATH, '//*[@id="xi-div-1"]/div[4]/label[2]/p').click()
        time.sleep(1)
        driver.find_element(By.ID, "applicationForm:managedForm:proceed").click()
        time.sleep(5)

    def execute_form_actions(self, driver):
        logging.info("Fill out form")
        # select Korea, Republik
        s = Select(driver.find_element(By.ID, "xi-sel-400"))
        s.select_by_visible_text(form_selections["nationality"])
        time.sleep(0.1)
        # eine person
        s = Select(driver.find_element(By.ID, "xi-sel-422"))
        s.select_by_visible_text(form_selections["num_applicants"])
        time.sleep(0.1)
        # with family
        s = Select(driver.find_element(By.ID, "xi-sel-427"))
        s.select_by_visible_text(form_selections["living_with_family"])
        time.sleep(0.1)
        if form_selections["living_with_family"].lower() == "ja":
            s = Select(driver.find_element(By.ID, "xi-sel-428"))
            s.select_by_visible_text(form_selections["family_nationality"])
        time.sleep(2)

        self.click_element_by_visible_text(driver, click_labels.get("visa_case"))

        self.click_element_by_visible_text(
            driver, click_labels.get("application_reason")
        )

        self.click_element_by_visible_text(
            driver,
            click_labels.get("detail_reason"),
        )
        time.sleep(5)

        # submit form
        driver.find_element(By.ID, "applicationForm:managedForm:proceed").click()
        time.sleep(5)

    def click_element_by_visible_text(self, driver, visible_text):
        try:
            # First, try to find a label that directly contains the visible text
            elements = driver.find_elements(
                By.XPATH, f"//label[contains(., '{visible_text}')]"
            )
            if elements:
                for element in elements:
                    if element.text.strip() == visible_text:
                        element.click()
                        logging.info(
                            f"Clicked on the label with text '{visible_text}' successfully."
                        )
                        time.sleep(
                            1
                        )  # Adding sleep to allow any dynamic reactions to the click
                        return
            else:
                # If direct label wasn't found or clicked, look for <p> containing the text, inside a label
                p_element = driver.find_element(
                    By.XPATH, f"//label/p[contains(., '{visible_text}')]"
                )
                if p_element:
                    p_element.click()
                    logging.info(
                        f"Clicked on the <p> element with text '{visible_text}' successfully."
                    )
                    time.sleep(
                        1
                    )  # Adding sleep to allow any dynamic reactions to the click
        except Exception as e:
            logging.error(
                f"Error clicking on the element with text '{visible_text}': {e}. Please double check if your text is correct in German."
            )

    def click_element(self, driver, xpath):
        element = driver.find_element(By.XPATH, xpath)
        element.click()
        time.sleep(1)  # Provides a buffer between actions

    def select_by_text(self, driver, element_id, text):
        select_element = Select(driver.find_element(By.ID, element_id))
        select_element.select_by_visible_text(text)
        time.sleep(1)  # Provides a buffer between actions

    def _send_slack_notification(self, driver: webdriver.Chrome):
        if self.slack_webhook_url is None:
            # Don't use slack.
            return True
        try:
            current_url = driver.current_url  # Get the current URL from the WebDriver
            message_text = f"Termin is Available! Check it out here: {current_url}"  # Include the URL in the message text
            message = {"text": message_text}
            try:
                response = requests.post(
                    self.slack_webhook_url, json=message, timeout=5
                )  # It's a good practice to set a timeout
                response.raise_for_status()  # This will raise an HTTPError if the response was an error status
            except (
                requests.exceptions.RequestException
            ) as e:  # This catches all exceptions raised by requests
                logging.error(f"Failed to send Slack notification due to: {e}")
        except Exception as e:
            current_url = f"Not available url. Error note: {e}"

    def _play_sound(self):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(self.sound_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
        except pygame.error as e:
            print(f"Skipping sound due to error: {e}")

    def handle_success(self, driver):
        logging.info("!!!SUCCESS - do not close the window!!!!")
        while True:
            try:
                self._send_slack_notification(driver)
                self._play_sound()
                time.sleep(
                    15
                )  # This will wait for 15 seconds before continuing with the next iteration.
            except KeyboardInterrupt:  # Catching the interrupt signal
                logging.info("Keyboard interrupt received, exiting...")
                break  # Exiting the loop
            except (
                Exception
            ) as e:  # This catches all other exceptions and keeps the loop running
                logging.info(
                    f"Error encountered: {e} - during SUCCESS to minimize the risk of closing the tab."
                )

    def run_once(self):
        with WebDriver(self.mode) as driver:
            self.enter_start_page(driver)
            self.tick_off_agreement(driver)
            self.execute_form_actions(driver)
            time.sleep(self.wait_time)

            # retry submit
            for _ in range(16):
                if not self.error_message in driver.page_source:
                    self.handle_success(driver)
                logging.info("Retry submitting form")
                driver.find_element(
                    By.ID, "applicationForm:managedForm:proceed"
                ).click()
                time.sleep(self.wait_time)

    def run_loop(self):
        logging.info("Sound Test! You will hear the same sound when it succeeds!")
        self._play_sound()
        idx = 0
        while True:
            logging.info(f"Iteration over {idx} times.")
            self.run_once()
            # Add any conditional checks or success handling here


if __name__ == "__main__":
    if len(sys.argv) == 1:
        mode = "local"
    elif len(sys.argv) == 2:
        # Extract command-line arguments
        mode = sys.argv[1]

    else:
        print("Usage: python3 macro_termin.py arg1")
        sys.exit(1)

    bot = MacroTermin(mode=mode)
    bot.run_loop()
