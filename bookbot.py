from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from datetime import datetime, timedelta
import random
import json
import time

def check_time_in_range(tee_time, time_low, time_high, time_format='%H:%M'):

    time_low = datetime.strptime(time_low, time_format).time()
    tee_time = datetime.strptime(tee_time, time_format).time()
    time_high = datetime.strptime(time_high, time_format).time()

    return tee_time >= time_low and tee_time <= time_high

def button_status(button):
    try:
        return button.is_enabled() and button.is_displayed()
    except:
        print('Failed to find button by name')
        return False

class Booking(object):

    def __init__(self, username, password, test=False):

        self.username = username
        self.password = password
        # self.payment_info = json.load(open('./payment.json'))
        ### run the script headless so a window doesn't pop out
        options = Options()
        options = webdriver.ChromeOptions()
        if not test:
            options.add_argument("--headless")

        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

        driver.set_page_load_timeout(10)
        driver.maximize_window()

        self.driver = driver

        self.runs = 0

    def enter_cc_info_van_parks(self):

        ### reserve selected tee time
        self.driver.switch_to.frame("mainIframe")
        add_st_num = self.driver.find_element(By.NAME, "avs_str_num")
        add_st_num.send_keys(self.payment_info['street_num'])

        add_st_name = self.driver.find_element(By.NAME, "avs_str_name")
        add_st_name.send_keys(self.payment_info['street_name'])

        add_postal_code = self.driver.find_element(By.NAME, "avs_zip_code")
        add_postal_code.send_keys(self.payment_info['postal_code'])

        cc_cardholder = self.driver.find_element(By.NAME, "cardholder")
        cc_cardholder.send_keys(self.payment_info['cardholder_name'])

        cc_num = self.driver.find_element(By.NAME, "pan")
        cc_num.send_keys(self.payment_info['cc_num'])

        cc_exp_month = self.driver.find_element(By.NAME, "exp_month")
        cc_exp_month.send_keys(self.payment_info['exp_month'])

        cc_exp_year = self.driver.find_element(By.NAME, "exp_year")
        cc_exp_year.send_keys(self.payment_info['exp_year'])

        cc_sec_code = self.driver.find_element(By.NAME, "cvd_value")
        cc_sec_code.send_keys(self.payment_info['sec_code'])

        time.sleep(random.uniform(0.1, 0.5))
        CCSubmitBtn = WebDriverWait(self.driver, 4).until(EC.element_to_be_clickable((By.NAME, "process"))).click()
        self.driver.switch_to.default_content()

        time.sleep(random.uniform(0.1, 0.5))
        ReserveBtnNext = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.NAME, "option"))).click()

    def get_vancouver_parks_times(self, course, days_in_advance,
                                  group_size=3, time_of_day='Anytime',
                                  early_time='7:45', late_time='9:00', fallback=True,
                                  booking_fee=False,
                                  group=1
                                 ):

        ### url constructors
        # logon_url = 'https://secure.west.prophetservices.com/CityofVancouver/Account/nLogOn?IsRequseLogin=True#Hash'
        logon_url = 'https://secure.west.prophetservices.com/CityofVancouver/Account/nLogOn'
        book_url = "https://secure.west.prophetservices.com/CityofVancouver/Home/nIndex?CourseId={courses}&Date={book_date}&Time={time}&Player={group_size}&Hole=18"

        ### course ids for url constructor
        course_ids = {
            'langara' : 1,
            'fraserview' : 2,
            'mccleery' : 3
        }

        ### date to book tee times for url constructor
        book_date = (datetime.now() + timedelta(days=days_in_advance)).date().strftime('%Y-%m-%d')

        ### first visit logon page to authenticate account
        self.driver.get(logon_url)
        UsernameInput = self.driver.find_element(By.NAME, "Email")
        UsernameInput.send_keys(self.username)
        PasswordInput = self.driver.find_element(By.NAME, "Password")
        PasswordInput.send_keys(self.password)
        self.driver.find_element(By.LINK_TEXT, "Sign In").click()

        ### retrieve tee times for selected course / date
        self.driver.get(book_url.format(
            courses=course_ids[course],
            book_date=book_date,
            time=time_of_day,
            group_size=group_size
        )
                  )

        ### select tee time from tee sheet
        tee_sheet = self.driver.find_element(By.CLASS_NAME, "container-fluid.teeSheet")
        tee_times = self.driver.find_elements(By.CLASS_NAME, "col-xs-12.col-sm-6.col-md-4.col-lg-3.teetime ")

        tee_index = [i for i, tee in enumerate(tee_times) if check_time_in_range(tee.get_attribute('teeTime'), early_time, late_time)]

        if tee_index:
            tee_time = tee_times[tee_index[group-1]]

        elif fallback:
            tee_time = tee_times[0]

        else:
            print(f"No Available Tee Times in Range") ### Re-try with a different date / range
            return

        tee_time_str = tee_time.get_attribute('teeTime')

        ### If there is already a reservation, the script will fail as you can't have conflicting tee times
        tee_time.click() ### can write a function here to select a tee time that matches a ToD criteria or first

        ### this button does not need to be used when the group is set in the url constructor
        # tee_time_next_btn = WebDriverWait(self.driver, 1.5).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Next']"))).click()
        time.sleep(random.uniform(0.1, 1))

        ### Since there can be two "submit" buttons check to see if you can use the card on file first!
        # payment_btn = self.driver.find_element(By.NAME, "submit")
        selectable = self.driver.find_elements(By.NAME, "submit")
        ### if there are submit buttons it means the tee times were selectable
        if selectable:

            payment_btn = self.driver.find_element(By.ID, "monerisCardOnFile")

            if button_status(payment_btn):
                payment_btn.click()

            elif booking_fee:
                ### click booking fee box before submit button is clickable
                terms_and_conditions = self.driver.find_elements(By.CLASS_NAME, "cbx-label")
                if terms_and_conditions:
                    self.driver.find_element(By.CLASS_NAME, "cbx-icon").click()
                    if button_status(payment_btn):
                        payment_btn.click()
            else:
                ### try to enter credit card info as last effort
                try:
                    payment_btn = self.driver.find_element(By.ID, "enterCCInfo")
                    self.enter_cc_info_van_parks()
                except Exception as e:
                    print(e)
                    return None
        else:
            ### if payment buttons are not present, this means there are conflicting tee times on the account
            print('There are potentially conflicting tee times')
            return None
        #
        time.sleep(random.uniform(0.1, 0.5))
        # CCSubmitBtn = WebDriverWait(self.driver, 4).until(EC.element_to_be_clickable((By.NAME, "process"))).click()
        # self.driver.switch_to.default_content()
        ReserveBtnConfirm = self.driver.find_element(By.NAME, "Option").click()

        print(f"{course} successfully booked on {book_date} at {tee_time_str}")
        return True

    def get_chronogolf_times(self, course, days_in_advance,
                             group_size=3, earliest='7:45',
                             latest='9:00', fallback=True ):

        course_links = {
            'tsawwassen' : 'https://www.chronogolf.ca/club/tsawwassen-springs-golf#?date={book_date}&nb_holes=18',
            'ubc' : 'https://www.chronogolf.ca/club/university-golf-club#?date={book_date}&nb_holes=18'
        }

        ### logon url
        logon_url = 'https://www.chronogolf.ca/'
        self.driver.get(logon_url)

        self.driver.find_element(By.CLASS_NAME, "site-head-login.ng-binding").click()
        UsernameInput = self.driver.find_element(By.NAME, "email")
        UsernameInput.send_keys(self.username)
        PasswordInput = self.driver.find_element(By.NAME, "password")
        PasswordInput.send_keys(self.password)
        self.driver.find_element(
            By.CLASS_NAME,
            "fl-button.fl-button-primary.fl-button-large.fl-button-block").click()

        book_url = course_links[course]

        book_date = (datetime.now() + timedelta(days=days_in_advance)).date().strftime('%Y-%m-%d')

        ### give script a second to load the authentication token before going to booking url
        time.sleep(1)
        self.driver.get(book_url.format(
            book_date=book_date
        )
                  )

        try:
            ### sometimes chronogolf makes you select 18 holes even if speicifc shuch in the url
            WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((
                By.CLASS_NAME,
                "fl-button.fl-button-large.fl-button-block.fl-button-primary.ng-binding"))
                                                 ).click()

        except:
            pass

        ### select the number of players in the group
        WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((
            By.CLASS_NAME,
            "toggler-heading.fl-button.fl-button-neutral.ng-pristine.ng-untouched.ng-valid.ng-binding.ng-scope.ng-empty"))
                                             )
        num_players = self.driver.find_elements(
            By.CLASS_NAME,
            "toggler-heading.fl-button.fl-button-neutral.ng-pristine.ng-untouched.ng-valid.ng-binding.ng-scope.ng-empty"
        )
        num_players[group_size - 1].click()
        ### select best tee time
        try:
            WebDriverWait(self.driver, 1.5).until(EC.element_to_be_clickable((
                By.CLASS_NAME,
                "fl-button.fl-button-large.fl-button-block.fl-button-primary.ng-binding"))
                                                 )

            self.driver.find_element(
                By.CLASS_NAME,
                "fl-button.fl-button-large.fl-button-block.fl-button-primary.ng-binding").click()


            WebDriverWait(self.driver, 4).until(EC.presence_of_element_located((
                By.CLASS_NAME,
                "widget-teetime"))
                                                 )

            tee_times_attr = self.driver.find_elements(By.CLASS_NAME, "widget-teetime") # get times
            tee_times_select = self.driver.find_elements(By.CLASS_NAME, "widget-teetime-wrapper") # select times


            tee_index = [i for i, tee in enumerate(tee_times_attr) \
                         if check_time_in_range(tee.get_attribute('innerText').split('\n')[0] ,
                                                earliest,
                                                latest,
                                                '%H:%M %p'
                                               )]

            if tee_index:
                tee_time_str = tee_times_attr[tee_index[0]].get_attribute('innerText').split('\n')[0]
                tee_times_select[tee_index[0]].click()

            elif fallback:
                tee_time_str = tee_times_attr[0].get_attribute('innerText').split('\n')[0]
                tee_times_select[0].click()

            else:
                print(f"No Available Tee Times in Range")

        except Exception as err:

            print(f"No Available Tee Times in Range")
            raise

        ### confirm selection
        self.driver.find_element(
            By.CLASS_NAME,
            "fl-button.fl-button-block.fl-button-large.fl-button-primary.ng-binding.ng-scope"
        ).click()

        ### accept ToS
        time.sleep(random.uniform(0.1, 1))
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((
            By.CLASS_NAME,
            "fl-checkbox-input.ng-pristine.ng-untouched.ng-empty.ng-invalid.ng-invalid-required"))
                                             )

        self.driver.find_element(
            By.CLASS_NAME,
            "fl-checkbox-input.ng-pristine.ng-untouched.ng-empty.ng-invalid.ng-invalid-required"
        ).click()

        ### confirm selection
        time.sleep(random.uniform(0.1, 1))
        self.driver.find_element(
            By.CLASS_NAME,
            "fl-button.fl-button-large.fl-button-primary.fl-button-block.ng-binding"
        ).click()

        print(f"{course} successfully booked on {book_date} at {tee_time_str}")
