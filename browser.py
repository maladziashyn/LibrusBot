import chromedriver_autoinstaller
import os
import platform
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as exp_cond
from selenium.webdriver.support.ui import WebDriverWait


class Browser:
    DELAY = 10
    URL_LOGIN = "https://portal.librus.pl/rodzina/synergia/loguj"
    URL_OGLOSZENIA = "https://synergia.librus.pl/ogloszenia"
    URL_WIADOMOSCI = "https://synergia.librus.pl/wiadomosci"

    def __init__(self, logger, download_path):
        self.logger = logger
        self.download_path = download_path

        chromedriver_autoinstaller.install()

        self.chrome_userdata = os.path.join(
            dict(os.environ)["LOCALAPPDATA"],
            "Google\\Chrome\\User data\\Default"
        ) if platform.system()[:3].lower() == 'win' else os.path.join(
            dict(os.environ)["HOME"],
            ".config\\google-chrome\\Default"
        )

        self.options = webdriver.ChromeOptions()

        self.options.add_experimental_option("detach", True)
        self.options.add_experimental_option("useAutomationExtension", False)
        self.options.add_experimental_option(
            "excludeSwitches",
            ["enable-automation"]
        )
        # self.options.add_argument('--headless')
        # self.options.add_argument('--no-sandbox')
        self.options.add_argument(f"user-data-dir={self.chrome_userdata}")
        self.options.add_experimental_option(
            "prefs",
            {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "download.default_directory": self.download_path,
            }
        )  # turn off chrome notification to 'save password', & download path

        self.b = webdriver.Chrome(options=self.options)
        self.b.maximize_window()

    def on_exception(self, exception_info):
        self.logger.exception(exception_info)
        sys.exit()

    def element_located(self, xpath, click=False, type_text=None,
                        switch_iframe=False):
        try:
            element = WebDriverWait(self.b, Browser.DELAY).until(
                exp_cond.presence_of_element_located((By.XPATH, xpath))
            )
            if click:
                element.click()
            if type_text:  # clear field & type text
                element.send_keys(Keys.CONTROL + "a")
                element.send_keys(type_text)
            if switch_iframe:
                self.b.switch_to.frame(element)
        except Exception as e:
            self.on_exception(e)

    def all_elements_located(self, xpath):
        """Return iterable of all elements located."""
        try:
            return WebDriverWait(self.b, Browser.DELAY).until(
                exp_cond.presence_of_all_elements_located((By.XPATH, xpath))
            )
        except Exception as e:
            self.on_exception(e)

    def page_loaded(self, xpath):
        try:
            WebDriverWait(self.b, Browser.DELAY).until(
                exp_cond.presence_of_element_located((By.XPATH, xpath))
            )
        except Exception as e:
            self.on_exception(e)

    def grab_attribute(self, xpath, attribute):
        try:
            element = WebDriverWait(self.b, Browser.DELAY).until(
                exp_cond.presence_of_element_located((By.XPATH, xpath))
            )
            return element.get_attribute(attribute)
        except Exception as e:
            self.logger.exception(e)
