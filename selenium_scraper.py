# from pyvirtualdisplay import Display
import os
import sys
import time

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from telegram import send_message, send_photo

load_dotenv()

URL_ID = os.getenv('URL_ID')
COUNTRY_CODE = os.getenv('COUNTRY_CODE')
BASE_URL = f'https://ais.usvisa-info.com/en-tr/niv'
MAIN_URL = f'https://ais.usvisa-info.com/en-{COUNTRY_CODE}/niv'
SCHEDULE_URL = os.getenv('SCHEDULE_URL')


def log_in(driver):
    if driver.current_url != BASE_URL + '/users/sign_in':
        print('Already logged.')
        print(driver.current_url)
        return

    print('Logging in.')

    # Clicking the first prompt, if there is one
    try:
        driver.find_element(By.XPATH, '/html/body/div/div[3]/div/button').click()
    except:
        pass
    # Filling the user and password
    user_box = driver.find_element(By.NAME, 'user[email]')
    user_box.send_keys(os.getenv('USERNAME'))
    password_box = driver.find_element(By.NAME, 'user[password]')
    password_box.send_keys(os.getenv('PASSWORD'))
    # Clicking the checkbox
    driver.find_element(By.XPATH, '//*[@id="sign_in_form"]/div/label/div').click()
    # Clicking 'Sign in'
    driver.find_element(By.XPATH, '//*[@id="sign_in_form"]/p/input').click()

    # Waiting for the page to load.
    # 5 seconds may be ok for a computer, but it doesn't seem enougn for the Raspberry Pi 4.
    time.sleep(10)
    print('Logged in.')


def has_website_changed(driver, url, no_appointment_text):
    '''Checks for changes in the site. Returns True if a change was found.'''
    # Log in
    while True:
        try:
            driver.get(url)
            log_in(driver)
            break
        except ElementNotInteractableException:
            time.sleep(5)

    # # For debugging false positives.
    # with open('debugging/page_source.html', 'w', encoding='utf-8') as f:
    #     f.write(driver.page_source)

    # Getting main text
    main_page = driver.find_element(By.ID, 'main')

    # For debugging false positives.
    with open('debugging/main_page', 'w') as f:
        f.write(main_page.text)

    # If the "no appointment" text is not found return True. A change was found.
    return no_appointment_text not in main_page.text

def getDates(driver):
    # Find all rows in the table body
    rows = driver.find_elements(By.XPATH, '//tbody/tr')

    # Initialize variables to store the dates
    ank_time = None
    ist_time = None

    # Iterate through each row to find the city and corresponding date
    for row in rows:
        city = row.find_element(By.XPATH, './td[1]').text
        date = row.find_element(By.XPATH, './td[2]').text.strip()  # Removing any leading/trailing whitespace
        
        if city == 'Ankara':
            ank_time = date
        elif city == 'Istanbul':
            ist_time = date

    return ist_time, ank_time

def get_schedule_page(driver):
    driver.get(SCHEDULE_URL)

def run_visa_scraper():
    # To run Chrome in a virtual display with xvfb (just in Linux)
    # display = Display(visible=0, size=(800, 600))
    # display.start()

    ist_time = None
    ank_time = None

    seconds_between_checks = 10 * 60

    # Setting Chrome options to run the scraper headless.
    chrome_options = Options()
    # chrome_options.add_argument("--disable-extensions")
    # chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--no-sandbox") # linux only
    if os.getenv('HEADLESS') == 'True':
        chrome_options.add_argument("--headless")  # Comment for visualy debugging

    # Initialize the chromediver (must be installed and in PATH)
    # Needed to implement the headless option
    driver = webdriver.Chrome(options=chrome_options)

    driver.get(BASE_URL + '/users/sign_in')
    log_in(driver)
    get_schedule_page(driver)

    first_run = True
    last_check_time = time.time()

    while True:
        current_time = time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime())
        print(f'Starting a new check at {current_time}.')
        print('\n')

        # Refresh the page
        driver.refresh()

        # store times
        new_ist_time, new_ank_time = getDates(driver)

        if time.time() - last_check_time >= 3600:  # 3600 seconds = 1 hour
            send_message("I'm here, everything is working fine.")
            last_check_time = time.time()  # Reset the timer

        if first_run:
            print("sending first times...")
            send_message(f'Available appointment times for İstanbul {ist_time}, for Ankara {ank_time}')

        dates_changed = new_ist_time != ist_time or new_ank_time != ank_time

        if dates_changed:
            ist_time = new_ist_time
            ank_time = new_ank_time
            
            print('A change was found. Notifying it.')
            print('\n')

            send_message(f'NEW available appointment time found!!! İstanbul {ist_time}, Ankara {ank_time}')
            send_photo(driver.get_screenshot_as_png())

            if "2024" in ist_time:
                send_message("CHECK OUT CHECK OUT!!! 2024 DATE FOUND!!")
                # driver.close()
                # exit()

        else:
            for seconds_remaining in range(int(seconds_between_checks), 0, -1):
                sys.stdout.write('\r')
                sys.stdout.write(
                    f'No change was found. Checking again in {seconds_remaining} seconds.'
                )
                sys.stdout.flush()
                time.sleep(1)
            print('\n')


def main():
    base_url = BASE_URL
    run_visa_scraper()


if __name__ == "__main__":
    main()
