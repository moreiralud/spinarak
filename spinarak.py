import chromedriver_autoinstaller, os, uuid, smtplib, time, base64, requests, json
from datetime import date
from bs4 import BeautifulSoup
from selenium import webdriver
from email.mime.text import MIMEText
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from dotenv import load_dotenv

load_dotenv()

sender_email = os.environ['GMAIL_SENDER']
receiver_email = os.environ['GMAIL_RECIPIENT']
receiver_email2 = os.environ['GMAIL_RECIPIENT_two']
password = os.environ['GMAIL_APP_PW']
CAPSOLVER_API_KEY = os.environ.get("CAPSOLVER_API_KEY")

num_iterations = 1
num_of_guests = 2
location = 'Tokyo'


def solve_captcha_with_capsolver(site_url):
    print("Solicitando resolução de CAPTCHA com CapSolver...")
    url = "https://api.capsolver.com/createTask"
    headers = {"Content-Type": "application/json"}
    payload = {
        "clientKey": CAPSOLVER_API_KEY,
        "task": {
            "type": "AntiAwsWafTaskProxyLess",
            "websiteURL": site_url
        }
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload)).json()
        if "errorCode" in response:
            print(f"Erro ao criar tarefa no CapSolver: {response}")
            return None

        task_id = response.get("taskId")
        print(f"Tarefa criada com sucesso. ID: {task_id}")

        result_url = "https://api.capsolver.com/getTaskResult"
        for attempt in range(30):
            print(f"Tentativa {attempt + 1}/30 para obter resultado...")
            time.sleep(5)
            result = requests.post(result_url, headers=headers, data=json.dumps({
                "clientKey": CAPSOLVER_API_KEY,
                "taskId": task_id
            })).json()

            if result.get("status") == "ready":
                print("CAPTCHA resolvido com sucesso.")
                return result["solution"]

        print("Tempo limite atingido para resolução do CAPTCHA.")
        return None

    except Exception as e:
        print(f"Erro ao comunicar com CapSolver: {e}")
        return None


def send_email(avail_slots, filename):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        subject = "Available days found by Spinarak bot: " + ' '.join(avail_slots)
        body = "Go check now!<br><br><a href='https://reserve.pokemon-cafe.jp/reserve/step1'>reserve.pokemon-cafe.jp</a><br><br>Available days:<br><br>"
        body += '<br>'.join(avail_slots)
        with open(filename, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read())
        body += '<br><img src="data:image/png;base64,' + encoded_string.decode() + '">'        
        message = MIMEText(body, 'html')
        message['Subject'] = subject
        message['From'] = sender_email
        message['To'] = receiver_email
        server.sendmail(sender_email, [receiver_email], message.as_string())
        server.sendmail(sender_email, [receiver_email2], message.as_string())
        print("Email enviado com sucesso!")
        server.quit()
    except Exception as e:
        print(f"Erro ao enviar email: {e}")


def create_booking(num_of_guests, location):
    if location == "Tokyo":
        website = "https://reserve.pokemon-cafe.jp/reserve/step1"
    elif location == "Osaka":
        website = "https://osaka.pokemon-cafe.jp/reserve/step1"

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--window-size=1200,1200")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

    driver = webdriver.Chrome(options=chrome_options)
    print("Navegador iniciado.")

    driver.get(website)
    time.sleep(2)

    if "Human Verification" in driver.title or "captcha" in driver.page_source.lower():
        print("CAPTCHA detectado. Iniciando resolução com CapSolver...")
        captcha_solution = solve_captcha_with_capsolver(website)
        if captcha_solution and "cookie" in captcha_solution:
            print("Injetando cookie de verificação no navegador...")
            driver.get("https://reserve.pokemon-cafe.jp/")
            cookie_raw = captcha_solution["cookie"]
            if ":" in cookie_raw:
                name, value = cookie_raw.split(":", 1)
                driver.add_cookie({
                    'name': name,
                    'value': value,
                    'domain': "reserve.pokemon-cafe.jp",
                    'path': '/',
                    'secure': True
                })
                print(f"Cookie injetado: name={name}, value={value[:10]}...")
            driver.get(website)
            time.sleep(2)
        else:
            print("Não foi possível resolver o CAPTCHA.")
            driver.quit()
            return

    print("Acessando a página de reservas...")

    try:
        select = Select(driver.find_element(By.NAME, 'guest'))
        time.sleep(2)
        select.select_by_index(num_of_guests)
        time.sleep(2)

        # Clica no "Next Month"
        try:
            next_month_btn = driver.find_element(By.XPATH, "//a[contains(text(), '次の月を見る')]")
            next_month_btn.click()
            print("Clicou em 'Next Month'")
            time.sleep(3)
        except Exception as e:
            print("Erro ao clicar em 'Next Month':", e)

        # Verifica se há dias disponíveis (sem a classe 'not-available')
        available_days = driver.find_elements(By.CSS_SELECTOR, ".calendar-day-cell:not(.not-available)")
        if available_days:
            print(f"Encontrou {len(available_days)} dia(s) disponível(is)!")
            available_slots = [day.text.strip() for day in available_days if day.text.strip()]

            filename = 'hits/pokemon-cafe-slot-found-' + date.today().strftime("%Y%m%d") + '-' + str(uuid.uuid4().hex) + '.png'
            driver.save_screenshot(filename)
            print(f"Screenshot salva em: {filename}")
            send_email(available_slots, filename)
        else:
            print("Nenhum dia disponível encontrado.")

        driver.quit()
    except NoSuchElementException:
        print("Elemento esperado não encontrado na página.")
        driver.quit()


chromedriver_autoinstaller.install()
[create_booking(num_of_guests, location) for _ in range(num_iterations)]
