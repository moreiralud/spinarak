import chromedriver_autoinstaller, os, uuid, random, smtplib, time, base64, requests, json
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
receiver_email2 = os.environ['GMAIL_RECIPIENT_two']
recipients = [os.environ['GMAIL_SENDER'], os.environ['GMAIL_RECIPIENT']]
password = os.environ['GMAIL_APP_PW']

# Capsolver API key
CAPSOLVER_API_KEY = os.environ.get("CAPSOLVER_API_KEY")

num_iterations = 10
day_of_month = '28'
num_of_guests = 2
location = 'Tokyo'

magic_cell = ''

def solve_captcha_with_capsolver(site_url):
    print("Solicitando resolução de CAPTCHA com CapSolver...")
    url = "https://api.capsolver.com/createTask"
    headers = {"Content-Type": "application/json"}
    payload = {
        "clientKey": CAPSOLVER_API_KEY,
        "task": {
            "type": "AntiAwsWafTask",
            "websiteURL": site_url
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload)).json()
    task_id = response.get("taskId")

    if not task_id:
        print("Erro ao criar tarefa no CapSolver:", response)
        return None

    print("Tarefa criada com sucesso. ID:", task_id)

    result_url = "https://api.capsolver.com/getTaskResult"
    for _ in range(30):
        time.sleep(5)
        res = requests.post(result_url, headers=headers, data=json.dumps({
            "clientKey": CAPSOLVER_API_KEY,
            "taskId": task_id
        })).json()

        if res.get("status") == "ready":
            print("CAPTCHA resolvido com sucesso!")
            return res["solution"]

        print("Aguardando resolução do CAPTCHA...")

    print("Tempo limite atingido para resolução do CAPTCHA.")
    return None

def send_email(avail_slots, filename):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        subject = "\U0001F6A8 Available days found by Spinarak bot: "
        for day in avail_slots:
            subject += day + ' '
        body = "Go check now!<br><br><a href ='https://reserve.pokemon-cafe.jp/reserve/step1'>reserve.pokemon-cafe.jp/reserve/step1</a><br><br>Available days:<br><br>"
        for day in avail_slots:
            body += day + '<br>'
        with open(filename, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read())
        body += '<br><img src="data:image/png;base64,' + encoded_string.decode() + '">'        
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
    if location == "Tokyo":
        website = "https://reserve.pokemon-cafe.jp/reserve/step1"
    elif location == "Osaka":
        website = "https://osaka.pokemon-cafe.jp/reserve/step1"

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--window-size=1200,1200")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)
    print("Navegador iniciado.")

    # Resolver CAPTCHA com CapSolver e adicionar cookie
    captcha_solution = solve_captcha_with_capsolver(website)
    if captcha_solution and "cookie" in captcha_solution:
        print("Injetando cookie de verificação no navegador...")
        driver.get("https://reserve.pokemon-cafe.jp/")
        driver.add_cookie({
            'name': captcha_solution['cookie']['name'],
            'value': captcha_solution['cookie']['value'],
            'domain': captcha_solution['cookie']['domain'],
            'path': '/',
            'secure': True
        })

    driver.get(website)
    print("Acessando a página de reservas...")

    try:
        driver.find_element(By.XPATH, "//*[@id=\"forms-agree\"]/div/div[1]/label").click()
        driver.find_element(By.XPATH, "//*[@id=\"forms-agree\"]/div/div[2]/button").click()
        time.sleep(random.randint(3, 6))
        driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div/a").click()
        time.sleep(random.randint(3, 6))
        select = Select(driver.find_element(By.NAME, 'guest'))
        time.sleep(random.randint(2, 3))
        select.select_by_index(num_of_guests)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        calendar_cells = soup.find_all("li")

        available = False
        available_slots = []
        global magic_cell
        for cell in calendar_cells:
            if "(full)" not in cell.text.lower() and "n/a" not in cell.text.lower():
                available_slots.append(cell.text.strip())
                available = True
                magic_cell = cell.text

        driver.execute_script('document.getElementsByTagName("html")[0].style.scrollBehavior = "auto"')
        element = driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[1]/p[3]")
        element.location_once_scrolled_into_view

        if available:
            print('Slot(s) AVAILABLE:')
            for day in available_slots:
                print(day + ' ')
            filename = 'hits/pokemon-cafe-slot-found-' + date.today().strftime("%Y%m%d") + '-' + str(uuid.uuid4().hex) + '.png'
            driver.save_screenshot(filename)
            send_email(available_slots, filename)
        else:
            print("No available slots found :(")

        driver.quit()
    except NoSuchElementException:
        print("Elemento esperado não encontrado na página.")
        driver.quit()

# Iniciar sessão virtual (caso necessário em ambientes headless)
display = Display(visible=0, size=(800, 800))
display.start()
chromedriver_autoinstaller.install()

[create_booking(day_of_month, num_of_guests, location) for x in range(num_iterations)]
