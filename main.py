import chromedriver_autoinstaller
import json
import logging
import os
import platform
import sys

from datetime import datetime
from pathlib import Path

from browser import Browser
from inbox import Ogloszenia, Wiadomosci
from telegram import Telegram

def main(logger, chrome, bot_token, bot_chat_id, user_creds):
    tg = Telegram(root_logger, bot_token, bot_chat_id)

    chrome.b.get(URL_LOGIN)

    # Accept cookies
    chrome.element_located(
        "//*[@id='consent-categories-description']/div[2]/div/div/button[2]",
        click=True,
        skip_elem=True
    )

    # Navigate to login menu
    chrome.element_located(
        "//a[@class='btn btn-third btn-synergia-top btn-navbar "
        "dropdown-toggle']",
        click=True
    )
    chrome.element_located(
        "//div[@class='dropdown-menu dropdown-menu--wide "
        "dropdown-menu--gray show']"
        "/a[@class='dropdown-item dropdown-item--synergia'][2]",
        click=True
    )

    # Switch to iframe
    chrome.element_located("//iframe[@id='caLoginIframe']", switch_iframe=True)

    # Enter login data and click "Zaloguj"
    chrome.element_located("//input[@id='Login']",
                           type_text=user_creds["login"])
    chrome.element_located("//input[@id='Pass']",
                           type_text=user_creds["password"])
    chrome.element_located("//button[@id='LoginBtn']",
                           click=True)
    chrome.b.switch_to.default_content()

    chrome.page_loaded("//div[@id='footer']")  # wait for full page load

    last_checked = datetime.strptime(user_creds["last checked"],
                                     "%Y-%m-%d %H:%M:%S")

    # WIADOMOŚĆI - odebrane
    # Go to "Wiadomośći" page
    chrome.b.get(URL_WIADOMOSCI)
    chrome.page_loaded("//div[@id='footer']")  # wait for full page load

    tb_html = chrome.grab_attribute("//table[@class='decorated stretch']",
                                    "innerHTML")
    wiad = Wiadomosci(logger, tb_html, datetime, last_checked)
    wiad.fill_wiad_dict(chrome)

    chrome.b.switch_to.default_content()

    # Wiadomośći
    tg.send_messages_list(
        [f"= = = {user_creds['name']}, {user_creds['type']} = = =",
         f"- - - WIADOMOŚĆI: {len(wiad.w_dict)} - - -"]
    )

    for idx, (key, value) in enumerate(wiad.w_dict.items()):
        msg = f"Nadawca: {value['Nadawca']}"
        msg += f"\nTemat: {value['Temat']}"
        msg += f"\nWysłano: {value['Wysłano']}"
        msg += f"\n\nTreść: {value['Treść']}"
        msg += f"\n\n- - - Koniec wiadomośći {idx + 1}/" \
               f"{len(wiad.w_dict)} - - -"
        msg += f"\n\nZałącznik: {value['Załącznik']}"

        if value['Załącznik'] == "TAK":
            msg += f" ({len(value['Pobrane'])})"

        tg.telegram_bot_sendtext(msg)

        if value["Załącznik"] == "TAK":
            for file in value["Pobrane"]:
                tg.telegram_bot_sendfile({"document": open(file, "rb")})

    # OGŁOSZENIA
    # Go to "Ogłoszenia" page
    if user_creds["type"] == "rodzic":
        chrome.b.get(URL_OGLOSZENIA)

        chrome.page_loaded("//div[@id='footer']")  # wait for full page load

        # Grab notifications' table html
        tb_html = chrome.grab_attribute("//div[@class='container-background']",
                                        "innerHTML")

        # Create Ogłoszenia DICT
        ogl = Ogloszenia(logger, tb_html, datetime, last_checked)
        ogl.fill_ogl_dict()
        ogl.create_tg_message()

        tg.send_messages_list(ogl.tg_message)



# USER_CREDS_PATH = "sample_user_creds.json"
USER_CREDS_PATH = "user_creds.json"
# TG_CREDS_PATH = "sample_tg_creds.json"
TG_CREDS_PATH = "tg_creds.json"

URL_LOGIN = "https://portal.librus.pl/rodzina/synergia/loguj"
URL_OGLOSZENIA = "https://synergia.librus.pl/ogloszenia"
URL_WIADOMOSCI = "https://synergia.librus.pl/wiadomosci"


if __name__ == '__main__':
    download_dir = os.path.join(Path.home(), "Downloads")
    chromedriver_autoinstaller.install()
    platf = platform.system()[:3].lower()
    if platf == "win":
        userdata_dir = os.path.join(dict(os.environ)["LOCALAPPDATA"],
                                    "Google\\Chrome\\User data\\Default")
    elif platf == "lin":
        userdata_dir = os.path.join(os.environ["HOME"],
                                  ".config\\google-chrome\\Default")
    else:
        sys.exit()

    logging.basicConfig(filename="logs.txt",
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        level=logging.WARNING)
    root_logger = logging.getLogger()

    # Grab User creds
    with open(USER_CREDS_PATH, "r") as f:
        user_credentials = json.load(f)

    # Grab TG creds
    with open(TG_CREDS_PATH, "r") as f:
        tg_credentials = json.load(f)

    updated_user_creds = list()
    for i in range(len(user_credentials)):
        browser = Browser(download_dir, userdata_dir, root_logger)

        check_time = datetime.strftime(datetime.now(),
                                       "%Y-%m-%d %H:%M:%S")
        main(root_logger, browser, tg_credentials['bot_token'],
             tg_credentials['bot_chat_id'], user_credentials[i])
        browser.b.close()
        browser.b.quit()

        # Update "last checked" date
        user_credentials[i]["last checked"] = check_time
        updated_user_creds.append(user_credentials[i])

    # Update "last checked" date in JSON
    with open(USER_CREDS_PATH, "w") as f:
        json.dump(updated_user_creds, f, indent=4)
