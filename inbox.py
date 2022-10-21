import os
import time

from bs4 import BeautifulSoup


class Ogloszenia:
    def __init__(self, logger, inner_html, datetime, last_checked):
        self.logger = logger
        self.inner_html = inner_html
        self.datetime = datetime
        self.last_checked = last_checked
        self.soup = BeautifulSoup(self.inner_html, "html.parser")

        self.ogl_dict = dict()
        self.count = 0
        self.tg_message = list()

    def fill_ogl_dict(self):
        for tbl in self.soup.find_all("table"):
            dt_issued = tbl.tbody.tr.find_next_sibling().td.text
            dt_issued_obj = self.datetime.strptime(dt_issued, "%Y-%m-%d")

            if dt_issued_obj >= self.last_checked:
                self.count += 1

                self.ogl_dict[f"item_{self.count}"] = dict()

                # Use "o" here for shorter referencing
                o = self.ogl_dict[f"item_{self.count}"]

                o["Tytuł"] = tbl.thead.tr.td.text
                o["Dodał"] = tbl.tbody.tr.td.text
                o["Data publikacji"] = tbl.tbody.tr.find_next_sibling().td.text
                o["Treść"] = tbl.tbody.tr.find_next_sibling().\
                    find_next_sibling().td.text

    def create_tg_message(self):
        self.tg_message.append(f"- - - OGŁOSZENIA: {self.count} - - -")
        all_ogloszenia = ""
        if self.count > 0:
            item_count = 1
            for item in self.ogl_dict.values():
                for key, value in item.items():
                    all_ogloszenia += f"{key}: {value}\n"
                all_ogloszenia += f"\n- - - Koniec ogłoszenia {item_count}/" \
                                  f"{self.count}. - - -\n\n\n"
                item_count += 1
        self.tg_message.append(all_ogloszenia)


class Wiadomosci:
    SLEEP_SECONDS = 3

    def __init__(self, logger, inner_html, datetime, last_checked):
        self.logger = logger
        self.inner_html = inner_html
        self.datetime = datetime
        self.last_checked = last_checked
        self.soup = BeautifulSoup(self.inner_html, "html.parser").tbody

        self.w_dict = dict()
        self.count = 0

    def fill_wiad_dict(self, browser):
        for row in self.soup.find_all("tr"):
            wyslano = row.td.next_sibling.next_sibling.next_sibling.\
                next_sibling.next_sibling.next_sibling.next_sibling.text
            wyslano_dt_obj = self.datetime.strptime(wyslano,
                                                    "%Y-%m-%d %H:%M:%S")

            if wyslano_dt_obj >= self.last_checked:
                self.count += 1

                self.w_dict[f"item_{self.count}"] = dict()
                # Use "w" here for shorter referencing
                w = self.w_dict[f"item_{self.count}"]

                nadawca = row.td.next_sibling.next_sibling.next_sibling.\
                    next_sibling
                w["Nadawca"] = nadawca.text.strip()
                temat = nadawca.next_sibling
                w["Temat"] = temat.text.strip()
                w["Wysłano"] = wyslano

                w["Załącznik"] = "Nie" \
                    if row.td.next_sibling.next_sibling.img is None \
                    else "TAK"

                # Grab hyperlinks
                w["Link"] = browser.grab_attribute(
                    f"//a[contains(text(), '{w['Temat']}')]",
                    "href"
                )

                # Go to email page
                browser.b.get(w["Link"])

                # Grab inner html & Treść
                wiad_html = browser.grab_attribute(
                    "//div[@class='container-message-content']",
                    "innerHTML"
                )

                soup = BeautifulSoup(wiad_html, "html.parser")
                w["Treść"] = soup.text

                if w["Załącznik"] == "TAK":
                    downloaded_files = list()

                    # Get files names
                    tb_html = browser.grab_attribute(
                        "//table[@class='stretch container-message']/tbody/"
                        "tr/td[2]/table[3]/tbody",
                        "innerHTML")
                    soup = BeautifulSoup(tb_html, "html.parser")

                    zalaczniki = list()

                    for table_row in soup.find_all("tr"):
                        if "Pliki:" in table_row.td.text:
                            continue
                        else:
                            zalaczniki.append(table_row.td.text.strip())
                    w["Pliki"] = zalaczniki

                    # Download attachments
                    dl_buttons = browser.all_elements_located(
                        "//img[@src='/assets/img/homework_files_icons/"
                        "download.png']")

                    for count, button in enumerate(dl_buttons):
                        existing_downloaded_files = list()
                        for (dirpath, dirnames, filenames) in os.walk(
                                browser.download_path):
                            existing_downloaded_files.extend(filenames)
                            break

                        button.click()

                        fully_downloaded = False
                        while not fully_downloaded:
                            # Get list of all files in downloads directory
                            dloaded = []
                            for (dirpath, dirnames, filenames) in os.walk(
                                    browser.download_path):
                                dloaded.extend(filenames)
                                break

                            if len(dloaded) == len(existing_downloaded_files):
                                time.sleep(Wiadomosci.SLEEP_SECONDS)
                            else:
                                # Ensure there's no .crdownload and .tmp
                                if all([".crdownload" not in f
                                        and ".tmp" not in f
                                        for f in dloaded]):
                                    # Find downloaded file
                                    file_to_append = list(
                                        set(dloaded)
                                        - set(existing_downloaded_files)
                                    )[0]
                                    downloaded_files.append(
                                        os.path.join(browser.download_path,
                                                     file_to_append))
                                    fully_downloaded = True
                                    # break
                                else:
                                    time.sleep(Wiadomosci.SLEEP_SECONDS)
                        browser.b.switch_to.window(browser.b.window_handles[1])
                        browser.b.close()
                        browser.b.switch_to.window(browser.b.window_handles[0])
                    # and lastly add the list of downloaded filepaths
                    # to Wiadomośći dictionary
                    w["Pobrane"] = downloaded_files
                browser.b.back()
            else:
                break
