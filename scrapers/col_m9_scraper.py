import re
import time
import os
import traceback
from datetime import datetime
import glob
import json
import pprint
import timeit
# Local imports
from classes.author import Author
from common.errors import GeneralError
from common.enums import AzureResponse
from common.helpers.methods.common_scrape_helpers.check_download_finish import check_download_finish
from common.helpers.methods.common_scrape_helpers.clear_directory import clear_directory
from common.helpers.methods.common_scrape_helpers.drgprk_helper import identify_article_type, reference_formatter
from common.helpers.methods.common_scrape_helpers.other_helpers import check_article_type_pass
from common.helpers.methods.scan_check_append.issue_scan_checker import is_issue_scanned
from common.helpers.methods.pdf_cropper import crop_pages, split_in_half
from common.services.azure.azure_helper import AzureHelper
from common.services.adobe.adobe_helper import AdobeHelper
from common.services.send_notification import send_notification
import common.helpers.methods.others
from common.services.tk_api.tk_service import TKServiceWorker
from scrapers.dergipark_scraper import update_scanned_issues
# 3rd Party libraries
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService

is_test = False
json_two_articles = True if is_test else False


def check_url(url):
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url


def get_logs_path(parent_type: str, file_reference: str) -> str:
    current_file_path = os.path.realpath(__file__)
    parent_directory_path = os.path.dirname(os.path.dirname(current_file_path))
    logs_path = os.path.join(parent_directory_path, "downloads_n_logs",
                             "col_m9_manual", parent_type,
                             file_reference, "logs")
    return logs_path


def get_downloads_path(parent_type: str, file_reference: str) -> str:
    current_file_path = os.path.realpath(__file__)
    parent_directory_path = os.path.dirname(os.path.dirname(current_file_path))
    downloads_path = os.path.join(parent_directory_path, "downloads_n_logs",
                                  "col_m9_manual", parent_type,
                                  file_reference, "downloads")
    return downloads_path


def get_recently_downloaded_file_name(download_path, journal_name, article_url):
    """
    Give the full PATH of the most recently downloaded file
    :param journal_name: Name of the journal
    :param article_url: URL of the article page
    :param download_path: PATH of the download folder
    :return: Returns the name of the most recently downloaded file
    """
    time.sleep(2)
    try:
        list_of_files = glob.glob(download_path + '/*')
        latest_file = max(list_of_files, key=os.path.getctime)
        return latest_file
    except Exception as e:
        send_notification(GeneralError(f"Could not get name of recently downloaded file. Journal name: {journal_name}, "
                                       f"article_url: {article_url}. Error: {e}"))
        return False


def update_authors_with_correspondence(paired_authors, correspondence_name, correspondence_mail):
    """

    :param paired_authors:
    :param correspondence_name:
    :param correspondence_mail:
    :return:
    """
    for author in paired_authors:
        if common.helpers.methods.others.similarity(author.name, correspondence_name) > 80:
            author.is_correspondence = True
            author.mail = correspondence_mail
    return paired_authors


def create_logs(was_successful: bool, path_: str) -> None:
    """
    Creates a logs file in the given path
    :param was_successful: If the trial was successful, then True, else False
    :param path_: PATH value of logs file
    :return: Nothing
    """
    try:
        logs_file_path = os.path.join(path_, 'logs.json')
        if was_successful:
            with open(logs_file_path, 'r') as logs_file:
                logs_data = json.loads(logs_file.read())
        logs_data.append({'timeOfTrial': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                          'attemptStatus': was_successful})
        with open(logs_file_path, 'w') as logs_file:
            logs_file.write(json.dumps(logs_data, indent=4))

    except Exception as e:
        send_notification(
            GeneralError(f"Error encountered while updating col_m9 journal logs file with path = {path_}. "
                         f"Error encountered: {e}."))


def log_already_scanned(path_: str):
    """
    This function will create a log file for the already scanned issues.
    :param path_: PATH value of the logs file
    :return: None
    """
    try:
        logs_path = os.path.join(path_, "logs.json")
        with open(logs_path, 'r') as logs_file:
            logs_data = json.loads(logs_file.read())
        logs_data.append({'timeOfTrial': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                          'attemptStatus': 'Already Scanned - No Action Needed'})
        with open(logs_path, 'w') as logs_file:
            logs_file.write(json.dumps(logs_data, indent=4))
    except Exception as e:
        send_notification(
            GeneralError(
                f"Already scanned issue log creation error for col_m9 journal with path = {path_}. Error: {e}"))


def check_scan_status(**kwargs):
    try:
        return is_issue_scanned(kwargs["vol"], kwargs["issue"], kwargs["logs_path"])
    except Exception as e:
        send_notification(
            GeneralError(f"Error encountered while checking issue scan status for col_m9 journal "
                         f"with path = {kwargs['logs_path']}, (check_scan_status, col_m9_scraper.py). Error: {e}"))
        raise e


def populate_with_azure_data(final_article_data, azure_article_data):
    """
    if there are any missing data, it will be populated with azure data either titles, abstracts or keywords
    :param final_article_data:
    :param azure_article_data:
    :return:
    """
    if not final_article_data["articleTitle"]["TR"]:
        final_article_data["articleTitle"]["TR"] = azure_article_data.get("article_titles", {}).get("tr", "")
    if not final_article_data["articleTitle"]["ENG"]:
        final_article_data["articleTitle"]["ENG"] = azure_article_data.get("article_titles", {}).get("eng", "")
    if not final_article_data["articleAbstracts"]["TR"]:
        tr_abstract = azure_article_data.get("article_abstracts", {}).get("tr#1", "")
        tr_abstract2 = azure_article_data.get("article_abstracts", {}).get("tr#2", "")
        final_article_data["articleAbstracts"]["TR"] = tr_abstract + " " + tr_abstract2
    if not final_article_data["articleAbstracts"]["ENG"]:
        eng_abstract = azure_article_data.get("article_abstracts", {}).get("eng#1", "")
        eng_abstract2 = azure_article_data.get("article_abstracts", {}).get("eng#2", "")
        final_article_data["articleAbstracts"]["ENG"] = eng_abstract + " " + eng_abstract2
    if not final_article_data["articleKeywords"]["TR"]:
        final_article_data["articleKeywords"]["TR"] = azure_article_data.get("article_keywords", {}).get("tr", "")
    if not final_article_data["articleKeywords"]["ENG"]:
        final_article_data["articleKeywords"]["ENG"] = azure_article_data.get("article_keywords", {}).get("eng", "")
    if not final_article_data["articleType"]:
        final_article_data["articleType"] = "ORİJİNAL ARAŞTIRMA"
    if not final_article_data["articleAuthors"]:
        final_article_data["articleAuthors"] = azure_article_data.get("article_authors", [])
    if not final_article_data["articleDOI"]:
        final_article_data["articleDOI"] = azure_article_data.get("doi", None)    
    return final_article_data


def col_m9_scraper(journal_name, start_page_url, pdf_scrape_type, pages_to_send, parent_type, file_reference):
    # Webdriver options
    # Eager option shortens the load time. Driver also always downloads the pdfs and does not display them
    options = Options()
    options.page_load_strategy = 'eager'
    download_path = get_downloads_path(parent_type, file_reference)
    prefs = {"plugins.always_open_pdf_externally": True, "download.default_directory": download_path}
    options.add_experimental_option('prefs', prefs)
    options.add_argument("--disable-notifications")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--headless")
    service = ChromeService(executable_path=r"/home/ubuntu/driver/chromedriver-linux64/chromedriver")

    # Set start time
    start_time = timeit.default_timer()
    i = 0  # Will be used to distinguish article numbers

    try:
        with webdriver.Chrome(service=service, options=options) as driver:
            driver.get(check_url(start_page_url))
            driver.maximize_window()
            time.sleep(3)
            try:
                close_button = driver.find_element(By.XPATH, '//*[@id="dvPopupModal"]/button')
                close_button.click()
                time.sleep(2)
            except Exception:
                pass

            try:
                # get element with class name press-date journal-volume-info
                issue_data = driver.find_element(By.CLASS_NAME, "press-date.journal-volume-info")
                recent_issue = int(issue_data.text.split('\n')[1].split(':')[1].strip().split(' ')[0])
                recent_volume = int(issue_data.text.split('\n')[1].split(':')[2].strip())

                # col-m9 gives the name to the scraper and has the article elements
                col_m9_element = driver.find_element(By.CLASS_NAME, "col-md-9")
                document_detail_items = col_m9_element.find_elements(By.CLASS_NAME, "document-detail")
            except Exception as e:
                raise GeneralError(f"Error while getting recent volume or issue data or retrieving article elements of "
                                   f"col_m9 journal with name {journal_name}. Error encountered is {e}")

            is_issue_scanned = check_scan_status(logs_path=get_logs_path(parent_type, file_reference),
                                                 vol=recent_volume, issue=recent_issue, pdf_scrape_type=pdf_scrape_type)
            if not is_issue_scanned:
                if is_test:
                    update_scanned_issues(recent_volume, recent_issue,
                                          get_logs_path(parent_type, file_reference))
                article_urls = list()
                for item in document_detail_items:
                    item_article_type = item.find_element(By.TAG_NAME, "h3").text.strip()
                    item_pass = check_article_type_pass(identify_article_type(item_article_type, 0))
                    if not item_pass:
                        continue
                    try:
                        for url_item in item.find_elements(By.CSS_SELECTOR, ".document-detail > a"):
                            article_urls.append(url_item.get_attribute("href"))
                    except Exception as e:
                        send_notification(GeneralError(
                            f"Error while getting col_m9 article urls of journal: {journal_name}. "
                            f"Error encountered was: {e}"))

                for article_url in article_urls:
                    with_adobe, with_azure = True, True
                    driver.get(article_url)
                    time.sleep(3)
                    try:
                        column_bar = driver.find_element(By.CLASS_NAME, "col-md-3")
                        try:
                            download_link = column_bar.find_element(By.ID, 'ctl09_ArticleTools_aPdf').get_attribute('href')
                        except Exception as e:
                            download_link = None
                            send_notification(GeneralError(f"No download link found for col_m9 journal with name {journal_name}."))

                        file_name, location_header = None, None
                        if download_link:
                            driver.get(download_link)
                            if check_download_finish(download_path):
                                file_name = get_recently_downloaded_file_name(download_path, journal_name, article_url)
                            if not file_name:
                                with_adobe, with_azure = False, False
                            # Send PDF to Azure and format response
                            if with_azure:
                                first_pages_cropped_pdf = crop_pages(file_name, pages_to_send)
                                location_header = AzureHelper.analyse_pdf(
                                    first_pages_cropped_pdf,
                                    is_tk=False)  # Location header is the response address of Azure API
                        try:
                            article_data_element = driver.find_element(By.CSS_SELECTOR,
                                                                   ".document-detail.about.search-detail")
                        except Exception as e:
                            raise GeneralError(f"No main article data element found for col_m9 journal {journal_name},"
                                               f"with number {i}. Error encountered was: {e}")

                        # Type
                        try:
                            article_type = identify_article_type(
                            article_data_element.find_element(By.TAG_NAME, "h3").text.strip(), 0)
                        except Exception:
                            article_type = "ORİJİNAL ARAŞTIRMA"

                        # Title
                        article_title = article_data_element.find_element(By.CSS_SELECTOR,
                                                                          ".doc-title.doc-title-txt.text-decoration-none").text.strip()

                        # DOI
                        article_doi = article_data_element.find_elements(By.TAG_NAME, "p")[1].text.strip()

                        # Abbreviation
                        try:
                            full_abbreviation = article_data_element.find_element(By.CLASS_NAME,
                                                                                  "date-detail-txt").text.strip()
                            abbreviation = ''.join([_x for _x in full_abbreviation if _x.isalpha() or _x.isspace()])
                            abbreviation = abbreviation.strip()
                        except Exception:
                            abbreviation = journal_name

                        # Page range
                        try:
                            article_page_range = [int(full_abbreviation.split(':')[-1].split('-')[0]),
                                                  int(full_abbreviation.split(':')[-1].split('-')[1])]
                        except:
                            article_page_range = [0, 1]

                        # Authors
                        author_elements = article_data_element.find_element(By.CLASS_NAME, "mb-20")
                        authors = list()
                        for author_element in author_elements.find_elements(By.TAG_NAME, "li"):
                            author = Author()
                            try:
                                author.name = re.sub(r"[^a-zA-ZşüğıöçŞÜĞIİÖÇ\s]", "",
                                                     author_element.find_element(By.TAG_NAME, "span").text.strip())
                                # Author specialities are not available all the time
                                author.all_speciality = author_element.find_element(By.TAG_NAME, "span").get_attribute(
                                    "data-department").strip()

                                class_name = author_element.find_element(By.TAG_NAME, "span").get_attribute("class")
                                author.is_correspondence = True if class_name == "active inline-block-list-item" else False
                                authors.append(author)
                            except Exception as e:
                                send_notification(GeneralError(
                                    f"Error while getting col_m9 article authors' data of journal: {journal_name}. "
                                    f"Error encountered was: {e}"))
                        try:
                            language_selection_element = driver.find_element(By.ID, "ctl08_langArea2")
                        except Exception:
                            language_selection_element = None

                        if not language_selection_element:
                            navigation_bar = article_data_element.find_element(By.CSS_SELECTOR, ".nav.nav-tabs")
                            navigation_bar.find_elements(By.TAG_NAME, "li")[0].click()
                            # Note!
                            # The col_m9 type journals have the abstract in either Turkish or English but not both
                            # If there are two abstracts, the second ones should be gotten from Azure services
                            # Page language
                            if "Abstract" in navigation_bar.text:
                                page_language = "en"
                            else:
                                page_language = "tr"

                            nav_bar_elements = navigation_bar.find_elements(By.TAG_NAME, "li")
                            references = None
                            for item in nav_bar_elements:
                                if item.get_attribute('id') == "ctl09_liRef":
                                    item.click()
                                    time.sleep(0.75)
                                    references = article_data_element.find_element(By.CSS_SELECTOR,
                                                                                   ".detail-text.font-12").text
                                    references = references.split(
                                        '\n')  # Split the references string into a list of reference strings
                                    references = [reference_formatter(reference, False, count) for count, reference in
                                                  enumerate(references, start=1)]

                                elif item.get_attribute('id') == "ctl09_liAbstract":
                                    item.click()
                                    time.sleep(0.75)
                                    abstract_full = article_data_element.find_element(By.ID, "tabAbstract").text.strip()

                            if not references and download_link and file_name:
                                # Send PDF to Adobe and format response
                                if with_adobe:
                                    adobe_cropped = split_in_half(file_name)
                                    adobe_response = AdobeHelper.analyse_pdf(adobe_cropped, download_path)
                                    adobe_references = AdobeHelper.get_analysis_results(adobe_response)
                                    references = adobe_references

                            # Get Azure Data
                            azure_article_data = None
                            if download_link and location_header and with_azure:
                                azure_response_dictionary = AzureHelper.get_analysis_results(location_header, 60)
                                if azure_response_dictionary["Result"] != AzureResponse.FAILURE.value:
                                    azure_data = azure_response_dictionary["Data"]
                                    azure_article_data = AzureHelper.format_general_azure_data(azure_data)
                                    if len(azure_article_data["emails"]) == 1:
                                        for author in authors:
                                            author.mail = azure_article_data["emails"][
                                                0] if author.is_correspondence else None
                                else:
                                    with_azure = False

                            # Abstract
                            abstract = abstract_full[: abstract_full.index(
                                "Anahtar Kelimeler")].strip() if page_language == "tr" else abstract_full[
                                                                                            : abstract_full.index(
                                                                                                "Keywords")].strip()
                            # Keywords
                            keywords = abstract_full[abstract_full.index(
                                "Anahtar Kelimeler:") + 18:].strip() if page_language == "tr" else abstract_full[
                                                                                                   abstract_full.index(
                                                                                                       "Keywords:") + 10:].strip()
                            keywords = [keyword.strip() for keyword in keywords.split(',')]

                            final_article_data = {
                                "journalName": f"{journal_name}",
                                "articleType": article_type,
                                "articleDOI": article_doi,
                                "articleCode": abbreviation + f"; {recent_volume}({recent_issue}): "
                                                              f"{article_page_range[0]}-{article_page_range[1]}",
                                "articleYear": datetime.now().year,
                                "articleVolume": recent_volume,
                                "articleIssue": recent_issue,
                                "articlePageRange": article_page_range,
                                "articleTitle": {"TR": article_title if page_language == "tr" else None,
                                                 "ENG": article_title if page_language == "en" else None},
                                "articleAbstracts": {"TR": abstract if page_language == "tr" else None,
                                                     "ENG": abstract if page_language == "en" else None},
                                "articleKeywords": {"TR": keywords if page_language == "tr" else None,
                                                    "ENG": keywords if page_language == "en" else None},
                                "articleAuthors": Author.author_to_dict(authors) if authors else None,
                                "articleReferences": references if references else None,
                                "articleURL": article_url,
                                "temporaryPDF": ""}
                        else:
                            lang_button = driver.find_element(By.ID, "ctl08_lnkTr2")
                            driver.execute_script("arguments[0].click();", lang_button)
                            time.sleep(7)
                            article_data_element = driver.find_element(By.CSS_SELECTOR,
                                                                   ".document-detail.about.search-detail")

                            navigation_bar = article_data_element.find_element(By.CSS_SELECTOR, ".nav.nav-tabs")
                            navigation_bar.find_elements(By.TAG_NAME, "li")[0].click()

                            # Title
                            article_title_tr = article_data_element.find_element(By.CSS_SELECTOR,
                                                                              ".doc-title.doc-title-txt.text-decoration-none").text.strip()

                            nav_bar_elements = navigation_bar.find_elements(By.TAG_NAME, "li")
                            references = None
                            for item in nav_bar_elements:
                                if item.get_attribute('id') == "ctl09_liRef":
                                    item.click()
                                    time.sleep(0.75)
                                    references = article_data_element.find_element(By.CSS_SELECTOR,
                                                                                   ".detail-text.font-12").text
                                    references = references.split(
                                        '\n')  # Split the references string into a list of reference strings
                                    references = [reference_formatter(reference, False, count) for count, reference in
                                                  enumerate(references, start=1)]

                                elif item.get_attribute('id') == "ctl09_liAbstract":
                                    item.click()
                                    time.sleep(1.5)
                                    abstract_full = article_data_element.find_element(By.ID, "tabAbstract").text.strip()

                            if not references and download_link and file_name:
                                # Send PDF to Adobe and format response
                                if with_adobe:
                                    adobe_cropped = split_in_half(file_name)
                                    adobe_response = AdobeHelper.analyse_pdf(adobe_cropped, download_path)
                                    adobe_references = AdobeHelper.get_analysis_results(adobe_response)
                                    references = adobe_references

                            # Get Azure Data
                            azure_article_data = None
                            if download_link and location_header and with_azure:
                                azure_response_dictionary = AzureHelper.get_analysis_results(location_header, 60)
                                if azure_response_dictionary["Result"] != AzureResponse.FAILURE.value:
                                    azure_data = azure_response_dictionary["Data"]
                                    azure_article_data = AzureHelper.format_general_azure_data(azure_data)
                                    if len(azure_article_data["emails"]) == 1:
                                        for author in authors:
                                            author.mail = azure_article_data["emails"][
                                                0] if author.is_correspondence else None
                                else:
                                    with_azure = False

                            # Abstract
                            try:
                                abstract_tr = abstract_full[: abstract_full.index(
                                    "Anahtar Kelimeler")].strip()
                            except:
                                abstract_tr = abstract_full.strip()

                            # Keywords
                            try:
                                keywords_tr = abstract_full[abstract_full.index(
                                    "Anahtar Kelimeler:") + 18:].strip()
                                keywords_tr = [keyword.strip() for keyword in keywords_tr.split(',')]
                            except:
                                keywords_tr = []

                            # ENG

                            lang_button = driver.find_element(By.ID, "ctl08_lnkEng2")
                            driver.execute_script("arguments[0].click();", lang_button)
                            time.sleep(5)
                            article_data_element = driver.find_element(By.CSS_SELECTOR,
                                                                   ".document-detail.about.search-detail")

                            # Title
                            article_title_eng = article_data_element.find_element(By.CSS_SELECTOR,
                                                                              ".doc-title.doc-title-txt.text-decoration-none").text.strip()


                            navigation_bar = article_data_element.find_element(By.CSS_SELECTOR, ".nav.nav-tabs")
                            navigation_bar.find_elements(By.TAG_NAME, "li")[0].click()

                            nav_bar_elements = navigation_bar.find_elements(By.TAG_NAME, "li")
                            for item in nav_bar_elements:
                                if item.get_attribute('id') == "ctl09_liAbstract":
                                    item.click()
                                    time.sleep(0.75)
                                    abstract_full = article_data_element.find_element(By.ID, "tabAbstract").text.strip()

                            # Abstract
                            abstract_eng = abstract_full[: abstract_full.index(
                                "Keywords")].strip()
                            # Keywords
                            keywords_eng = abstract_full[abstract_full.index(
                                "Keywords:") + 10:].strip()

                            keywords_eng = [keyword.strip() for keyword in keywords_eng.split(',')]

                            final_article_data = {
                                "journalName": f"{journal_name}",
                                "articleType": article_type,
                                "articleDOI": article_doi,
                                "articleCode": abbreviation + f"; {recent_volume}({recent_issue}): "
                                                              f"{article_page_range[0]}-{article_page_range[1]}",
                                "articleYear": datetime.now().year,
                                "articleVolume": recent_volume,
                                "articleIssue": recent_issue,
                                "articlePageRange": article_page_range,
                                "articleTitle": {"TR": article_title_tr if article_title_tr else None,
                                                 "ENG": article_title_eng if article_title_eng else None},
                                "articleAbstracts": {"TR": abstract_tr if abstract_tr else None,
                                                     "ENG": abstract_eng if abstract_eng else None},
                                "articleKeywords": {"TR": keywords_tr if keywords_tr else None,
                                                    "ENG": keywords_eng if keywords_eng else None},
                                "articleAuthors": Author.author_to_dict(authors) if authors else None,
                                "articleReferences": references if references else None,
                                "articleURL": article_url,
                                "temporaryPDF": ""}
                        if with_azure:
                            final_article_data = populate_with_azure_data(final_article_data, azure_article_data)
                        if is_test:
                            pprint.pprint(final_article_data)

                        # Send data to Client API
                        tk_worker = TKServiceWorker()
                        final_article_data["temporaryPDF"] = tk_worker.encode_base64(file_name)
                        if is_test:
                            response = tk_worker.send_data(final_article_data)
                            if isinstance(response, Exception):
                                raise response
                        else:
                            response = tk_worker.send_data(final_article_data)
                            if isinstance(response, Exception):
                                raise response

                        i += 1  # Loop continues with the next article
                        clear_directory(download_path)

                        if is_test and i >= 2:
                            return 590
                    except Exception as e:
                        i += 1
                        clear_directory(download_path)
                        tb_str = traceback.format_exc()
                        send_notification(GeneralError(
                            f"Passed one article of - COL_M9 - journal {journal_name} with article number {i}. "
                            f"Error encountered was: {e}. Article URL: {article_url}.  Traceback: {tb_str}"))
                        continue

                # Successfully completed the operations
                create_logs(True, get_logs_path(parent_type, file_reference))
                update_scanned_issues(recent_volume, recent_issue,
                                      get_logs_path(parent_type, file_reference))
                return 590 if is_test else timeit.default_timer() - start_time
            else:  # Already scanned the issue
                log_already_scanned(get_logs_path(parent_type, file_reference))
                return 590 if is_test else 530  # If test, move onto next journal, else wait 30 secs before moving on
    except Exception as e:
        send_notification(GeneralError(f"An error encountered and caught by outer catch while scraping col_m9 journal "
                                       f"'{journal_name}' with article number {i}. Error encountered was: {e}."))
        clear_directory(download_path)
        return 590 if is_test else timeit.default_timer() - start_time
