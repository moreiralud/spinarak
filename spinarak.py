import chromedriver_autoinstaller, os, uuid, random, smtplib, time
from datetime import date
from bs4 import BeautifulSoup
from selenium import webdriver
from email.mime.text import MIMEText
from pyvirtualdisplay import Display
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

# Define your email settings as repo secrets
sender_email = os.environ['GMAIL_SENDER']
receiver_email = os.environ['GMAIL_RECIPIENT']
# in case you want to send to another email
receiver_email2 = os.environ['GMAIL_RECIPIENT_two']
recipients = [os.environ['GMAIL_SENDER'], os.environ['GMAIL_RECIPIENT']]
# password of the sender email
password = os.environ['GMAIL_APP_PW'] # https://myaccount.google.com/apppasswords

num_iterations = 10
day_of_month='28'
num_of_guests=2
location = 'Tokyo'
#location = 'Osaka'

magic_cell = ''

display = Display(visible=0, size=(800, 800))  
display.start()

chromedriver_autoinstaller.install()  # Check if the current version of chromedriver exists
                                      # and if it doesn't exist, download it automatically,
                                      # then add chromedriver to path

def send_email(avail_slots, filename):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        subject = "\U0001F6A8 Available days found by Spinarak bot: "
        for day in avail_slots:
            subject += day + ' '
        body = "Go check now!\n\n<a href ='https://reserve.pokemon-cafe.jp/reserve/step1'>reserve.pokemon-cafe.jp/reserve/step1</a><br><br>Available days:<br><br>"
        for day in avail_slots:
            body += day + '<br>'
        # include screenshot of calendar with available day(s)
        with open(filename, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read())
        body += '<br><img src="data:image/png;base64,' + encoded_string.decode() + '">'
        # data URI scheme test
        body += '<br><img src="data:image/png;base64,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">'
	#message = f"Subject: {subject}\n\n{body}"
        message = MIMEText(body, 'html')
        message['Subject'] = subject
        message['From'] = sender_email
        message['To'] = receiver_email
        server.sendmail(sender_email, [receiver_email], message.as_string())
        server.sendmail(sender_email, [receiver_email2], message.as_string())
        print("Email sent!")
        server.quit()
    except Exception as e:
        print(f"Email error: {str(e)}")

def create_booking(day_of_month, num_of_guests, location):
    '''Create a reservation for Pokemon Cafe in Tokyo
    Keyword arguments:
    day_of_month -- day of the month to book
    num_of_guests -- number of guests to book (1-8)
    '''

    if location == "Tokyo":
        website = "https://reserve.pokemon-cafe.jp/"
    elif location == "Osaka":
        website = "https://osaka.pokemon-cafe.jp/"

    chrome_options = webdriver.ChromeOptions()    
    # Add your options as needed    
    options = [
        # Define window size here
        "--window-size=1200,1200",
        "--ignore-certificate-errors"
 
        #"--headless",
        #"--disable-gpu",
        #"--window-size=1920,1200",
        #"--ignore-certificate-errors",
        #"--disable-extensions",
        #"--no-sandbox",
        #"--disable-dev-shm-usage",
        #'--remote-debugging-port=9222'
    ]

    for option in options:
        chrome_options.add_argument(option)
	    
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(website)

    try:
        # XPaths is what will likely have to be changed if this bot breaks due to the Pokemon Cafe site updating the XML responses
        # Chrome > Developer Tools > Elements > Inspect Element > Right-click selected HTML > Copy XPath
        driver.find_element(By.XPATH, "//*[@id=\"forms-agree\"]/div/div[1]/label").click()
        driver.find_element(By.XPATH, "//*[@id=\"forms-agree\"]/div/div[2]/button").click()
        time.sleep(random.randint(3, 6))
        driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div/a").click()
        time.sleep(random.randint(3, 6))
        select = Select(driver.find_element(By.NAME, 'guest'))
        time.sleep(random.randint(2, 3))
	
        select.select_by_index(num_of_guests)
        #time.sleep(random.randint(5, 10))

        # Check if the updated page indicates availability
        soup = BeautifulSoup(driver.page_source, "html.parser")
        # Find all calendar-day-cell elements
        calendar_cells = soup.find_all("li")
        #calendar_cells = soup.find_all("li", class_="calendar-day-cell")
      
        available = False
        # Check each calendar cell for availability
        available_slots = []
        global magic_cell
        for cell in calendar_cells:
            if "(full)" not in cell.text.lower() and "n/a" not in cell.text.lower():
                available_slots.append(cell.text.strip())
                available = True
                magic_cell = cell.text

        # scroll down before taking screenshot
        driver.execute_script('document.getElementsByTagName("html")[0].style.scrollBehavior = "auto"')
        element=driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[1]/p[3]")
        element.location_once_scrolled_into_view
        if available:
            print('Slot(s) AVAILABLE: ')
            for day in available_slots:
                print(day + ' ')
            filename = 'hits/pokemon-cafe-slot-found-' + date.today().strftime("%Y%m%d") + '-' + str(uuid.uuid4().hex) + '.png'
            driver.save_screenshot(filename)
            send_email(available_slots, filename)
        else:
            print("No available slots found :(")

        driver.quit()
    except NoSuchElementException:
        pass

[create_booking(day_of_month, num_of_guests, location) for x in range(num_iterations)]

# test
#send_email()
