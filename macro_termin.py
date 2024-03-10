import logging
import time
import requests
import yaml

from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

import pygame


# Load config
def load_config(file_path="config.yaml"):
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


config = load_config()

logging.basicConfig(
    format="%(asctime)s\t%(levelname)s\t%(message)s", level=logging.INFO
)


class WebDriver:
    def __init__(self, implicit_wait_time=20):
        self.implicit_wait_time = implicit_wait_time

    def __enter__(self):
        logging.info("Open browser")
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
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
    def __init__(self):
        self.wait_time = config["berlin_bot"]["wait_time"]
        self.sound_file = config["berlin_bot"]["sound_file"]
        self.error_message = config["berlin_bot"]["error_message"]
        self.slack_webhook_url = config["slack"]["webhook_url"]

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
        s.select_by_visible_text("Korea, Republik")
        # eine person
        s = Select(driver.find_element(By.ID, "xi-sel-422"))
        s.select_by_visible_text("eine Person")
        # with family
        s = Select(driver.find_element(By.ID, "xi-sel-427"))
        s.select_by_visible_text("ja")
        # Select Korea, Republik
        s = Select(driver.find_element(By.ID, "xi-sel-428"))
        s.select_by_visible_text("Korea, Republik")
        time.sleep(2)

        # apply for residence title
        driver.find_element(By.XPATH, '//*[@id="xi-div-30"]/div[1]/label/p').click()
        time.sleep(1)

        # click on family
        driver.find_element(
            By.XPATH, '//*[@id="inner-467-0-1"]/div/div[5]/label'
        ).click()
        time.sleep(1)

        # rp for spouse
        driver.find_element(
            By.XPATH, '//*[@id="inner-467-0-1"]/div/div[6]/div/div[3]/label'
        ).click()
        time.sleep(2)

        # submit form
        driver.find_element(By.ID, "applicationForm:managedForm:proceed").click()
        time.sleep(4)

    def click_element(self, driver, xpath):
        element = driver.find_element(By.XPATH, xpath)
        element.click()
        time.sleep(1)  # Provides a buffer between actions

    def select_by_text(self, driver, element_id, text):
        select_element = Select(driver.find_element(By.ID, element_id))
        select_element.select_by_visible_text(text)
        time.sleep(1)  # Provides a buffer between actions

    def _send_slack_notification(self):
        message = {"text": "Termin is Available!"}
        response = requests.post(self.slack_webhook_url, json=message)
        if response.status_code == 200:
            logging.info("Slack notification sent successfully")
        else:
            logging.error("Failed to send Slack notification")

    def _play_sound(self):
        pygame.mixer.init()
        pygame.mixer.music.load(self.sound_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)

    def handle_success(self):
        logging.info("!!!SUCCESS - do not close the window!!!!")
        while True:
            try:
                self._send_slack_notification()
                self._play_sound()
                time.sleep(15)
            except:
                logging.info(
                    "Error handling during SUCCESS to minimize the risk of closing the tab."
                )

    def run_once(self):
        with WebDriver() as driver:
            self.enter_start_page(driver)
            self.tick_off_agreement(driver)
            self.execute_form_actions(driver)
            time.sleep(self.wait_time)

            # retry submit
            for _ in range(10):
                if not self.error_message in driver.page_source:
                    self.handle_success()
                logging.info("Retry submitting form")
                driver.find_element(
                    By.ID, "applicationForm:managedForm:proceed"
                ).click()
                time.sleep(self.wait_time)

    def run_loop(self):
        logging.info("Sound Test!")
        self._play_sound()
        idx = 0
        while True:
            logging.info(f"Iteration over {idx} times.")
            self.run_once()
            # Add any conditional checks or success handling here


if __name__ == "__main__":
    bot = MacroTermin()
    bot.run_loop()
