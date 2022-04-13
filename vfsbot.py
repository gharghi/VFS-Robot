import json
import os
import socket
import time
import urllib

import requests
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from twocaptcha import TwoCaptcha

base_path = '/etc/VFS_Appointment/'
# base_path = './'

with open(base_path + 'secrets.json') as f:
    params = f.read()
secrets = json.loads(params)

with open(base_path + 'candidates.json') as f:
    names = f.read()
candidates = json.loads(names)

## VFS login email
email_str = secrets['username']
## VFS password
pwd_str = secrets['password']
two_captcha_key = secrets["two_captcha_key"]
google_key = secrets["google_key"]


def login(browser, solver):
    ## Login Page
    try:
        browser.get("https://visa.vfsglobal.com/irn/en/prt/book-an-appointment")  # Portugal
        # # browser.get("https://visa.vfsglobal.com/irn/en/fin/book-an-appointment") # FInland
        time.sleep(6)
        page_url = browser.find_elements(By.LINK_TEXT, "Book now")[0].get_attribute('href')

        browser.get(page_url)
        time.sleep(4)
        browser.find_element(By.NAME, 'EmailId').send_keys(email_str)
        browser.find_element(By.NAME, 'Password').send_keys(pwd_str)

    except Exception as e:
        log_telegram(e)
        log_telegram(browser.page_source)
        time.sleep(10)
        monitor_appointments()

    try:
        browser.find_element(By.ID, "CaptchaInputText")
        m = 'text'
    except:
        m = 're'

    if m == 'text':
        log_telegram('textCaptcha method chosen')
        # Download image
        with open('Logo.png', 'wb') as file:
            file.write(browser.find_element(By.XPATH, '//*[@id="CaptchaImage"]').screenshot_as_png)

        files = {'file': open(base_path + 'Logo.png', 'rb')}
        ## Solve textCAPCHA
        req_url = "http://2captcha.com/in.php"
        values = {'key': two_captcha_key}
        ## Send captcha request
        r = requests.post(req_url, files=files, data=values)
        req_id = r.text.split('|')[1]
        time.sleep(5)

        res_url = "https://2captcha.com/res.php?key=" + two_captcha_key + "&action=get&id=" + req_id
        res = urllib.request.urlopen(res_url)

        result_captcha = str(res.read()).split('|')[1].split("'")[0].upper()
        browser.find_element(By.ID, "CaptchaInputText").send_keys(result_captcha)
        log_telegram('textCaptcha resolved')


    else:
        log_telegram('reCaptcha method chosen')

        ## Solve reCAPCHA
        url = "http://2captcha.com/in.php?key=" + two_captcha_key + "&method=userrecaptcha&googlekey=" + google_key + "&pageurl=" + page_url
        ## Send captcha request
        req = urllib.request.urlopen(url)
        req_id = str(req.read()).split('|')[1].split("'")[0]
        log_telegram('Sent reCaptcha request')

        ## read the result
        result = True
        while result:
            time.sleep(10)
            url = "http://2captcha.com/res.php?key=" + two_captcha_key + "&action=get&id=" + str(req_id)
            res = urllib.request.urlopen(url)
            result_code = res.read().decode(res.headers.get_content_charset()).split('|')
            print(result_code)
            if result_code[0] == 'OK':
                result = False

        browser.execute_script(
            "document.getElementById('g-recaptcha-response').setAttribute('style','display:block;');")

        browser.find_element(By.ID, 'g-recaptcha-response').send_keys(result_code[1])

        log_telegram('reCaptcha resolved')

    browser.find_element(By.CLASS_NAME, 'submitbtn').click()
    time.sleep(12)
    log_telegram(browser.title)
    try:
        if browser.title == "VFS : HOME PAGE":
            log_telegram('Logged In')
            print('Login Successful')
            return True
        else:
            log_telegram('problem in login')
            return False
    except Exception as e:
        log_telegram(e)
        return False


# Send liveness logs to telegram channel
def log_telegram(msg, max=False):
    try:
        hst = socket.gethostname()
        url = "https://api.telegram.org/bot203336328:AAHs333oaKO-zu3Wb333UADbv2-g/sendMessage?chat_id=-1001338312&text=" + str(
            hst) + ":  " + str(msg)
        requests.post(url)
        if max:
            url = "https://api.telegram.org/bot2033376328:AAsd33EWoaKO-zuqWb333hRFUADbv2-g/sendMessage?chat_id=-10033922453&text=" + str(
                msg)
            requests.post(url)
        return True
    except:
        return True


def alert_for_appointment(browser, result):
    if result:
        log_telegram('There are appointments available!', True)
    else:
        log_telegram(browser.find_element(By.ID, "LocationError").text)


def check_appointment(browser):
    ## Returns a tuple, (Session expired, AppointmentAvailable)
    browser.find_elements(By.LINK_TEXT, "Schedule Appointment")[0].click()
    time.sleep(5)
    try:

        select = Select(browser.find_element(By.ID, 'MissionId'))
        select.select_by_value('14')
        time.sleep(3)
        select = Select(browser.find_element(By.ID, 'CountryId'))
        select.select_by_value('31')
        time.sleep(3)
        select = Select(browser.find_element(By.ID, 'LocationId'))
        select.select_by_value('444')  # Portugal
        time.sleep(3)
        select = Select(browser.find_element(By.ID, 'VisaCategoryId'))
        select.select_by_value('3616')
        time.sleep(3)

        text = browser.find_element(By.ID, "LocationError").text
        if text == "There are no open seats available for selected center - Portugal Visa Application Center, Tehran":
            os.system('echo \'{"result":0}\' > /etc/VFS_Appointment/result.json')
            return alert_for_appointment(browser, False)
        else:
            alert_for_appointment(browser, True)
            schedule_appointment(browser)
            os.system('echo \'{"result":1}\' > /etc/VFS_Appointment/result.json')
            return False

    except Exception as e:
        log_telegram(e)
        return False


def schedule_appointment(browser):
    try:
        # Iterate between given groups
        for group in candidates['groups']:
            # Click on register appointment button
            browser.find_elements(By.LINK_TEXT, "Schedule Appointment")[0].click()
            # browser.find_element(By.XPATH, '//*[@id="Accordion1"]/div/div[2]/div/ul/li[1]/a').click()
            time.sleep(3)
            # Define the center
            select = Select(browser.find_element(By.ID, 'MissionId'))
            select.select_by_value('14')
            time.sleep(3)
            select = Select(browser.find_element(By.ID, 'CountryId'))
            select.select_by_value('31')
            time.sleep(3)
            select = Select(browser.find_element(By.ID, 'LocationId'))
            # select.select_by_value('263') # Finland
            select.select_by_value('444')  # Portugal
            # Define the visa type
            time.sleep(3)
            select = Select(browser.find_element(By.ID, 'VisaCategoryId'))
            select.select_by_value(group['visaType'])
            time.sleep(3)
            # continue button
            browser.find_element(By.ID, "btnContinue").click()
            log_telegram('Went to add customer page')

            # Iterate between users in each group
            for candidate in group['names']:
                time.sleep(3)
                # add customer button
                try:
                    browser.find_elements(By.LINK_TEXT, "Add Customer")[0].click()
                except Exception as e:
                    return log_telegram(e, False)
                time.sleep(4)
                log_telegram('Add customer page opened')
                browser.find_element(By.ID, "PassportNumber").send_keys(candidate['passportNum'])
                browser.find_element(By.ID, "PassportExpiryDate").send_keys(candidate['passportExpiry'])
                browser.find_element(By.ID, "DateOfBirth").send_keys(candidate['birthday'])
                Select(browser.find_element(By.ID, 'NationalityId')).select_by_value('65')
                browser.find_element(By.ID, "FirstName").clear()
                browser.find_element(By.ID, "FirstName").send_keys(candidate['first'])
                browser.find_element(By.ID, "LastName").clear()
                browser.find_element(By.ID, "LastName").send_keys(candidate['last'])
                if candidate['gender'] == 'M':
                    Select(browser.find_element(By.ID, 'GenderId')).select_by_value('1')
                elif candidate['gender'] == 'F':
                    Select(browser.find_element(By.ID, 'GenderId')).select_by_value('2')
                browser.find_element(By.ID, "Mobile").clear()
                browser.find_element(By.ID, "Mobile").send_keys(candidate['mobile'])
                browser.find_element(By.ID, "validateEmailId").clear()
                browser.find_element(By.ID, "validateEmailId").send_keys(candidate['email'])
                time.sleep(3)
                browser.find_element(By.ID, "submitbuttonId").click()
                Alert(browser).accept()
                log_telegram(candidate['first'] + ' Registered')

            time.sleep(3)
            browser.find_element(By.XPATH, '//*[@id="ApplicantListForm"]/div[2]/input').click()
            log_telegram('All of candidates registered')

            # Select free date
            objts = browser.find_elements(By.CLASS_NAME, "fc-day")
            for obj in objts:
                if obj.value_of_css_property("background-color") == "rgba(188, 237, 145, 1)":
                    print(obj.value_of_css_property("background-color"))
                    print(obj)
                    obj.click()
                    break
            log_telegram('date chose')
            # Select Time
            browser.find_element(By.NAME, "selectedTimeBand").click()

            # Submit
            browser.find_element(By.ID, "btnConfirm").click()
            Alert(browser).accept()
            log_telegram("Appointment Registered")

    except Exception as e:
        log_telegram(e)


def check_session_expired(browser):
    try:
        if 'VFS' in browser.title:
            return False
        else:
            log_telegram("ًSession Expired")
            log_telegram(browser.page_source)
            log_telegram(
                "IP changed to: " + os.popen("/etc/VFS_Appointment/change_server").read() + "due to firewall block!")
            return True
    except Exception as e:
        log_telegram(e)


def check_firewall_block(browser):
    if "VFS" in browser.title:
        return False
    elif "Book" in browser.title:
        return False
    elif "denied" in browser.title:
        log_telegram("Firewall Blocked")
        return True
    else:
        log_telegram("Firewall Blocked")
        return True


def monitor_appointments():
    try:
        log_telegram("Start the process")
        log_telegram("IP changed to: " + os.popen("/etc/VFS_Appointment/change_server").read() + "due to first run")
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("start-maximized")
        browser = uc.Chrome(options=chrome_options)
        solver = TwoCaptcha(two_captcha_key)

    except Exception as e:
        log_telegram(e)
        monitor_appointments()

    while True:
        try:
            login(browser, solver)
            if check_firewall_block(browser):
                log_telegram("IP changed to: " + os.popen(
                    "/etc/VFS_Appointment/change_server").read() + "due to firewall block!")
                continue
            try:
                i = 0
                while True:
                    i += 1
                    check_appointment(browser)
                    if check_session_expired(browser):
                        break
                    if i % 2 == 0:
                        log_telegram("IP changed to: " + os.popen("/etc/VFS_Appointment/change_server").read())
                    time.sleep(25)  # Sleep between checks
            except Exception as e:
                time.sleep(20)  # sleep for unknown error
                log_telegram(e)
        except Exception as e:
            log_telegram(e)
            time.sleep(120)  # Sleep between login fail detection


try:
    monitor_appointments()

except Exception as e:
    log_telegram(e)
