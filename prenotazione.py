from selenium.webdriver import Chrome
# from webdriver_manager.chrome import ChromeDriverManager  # not needed with system chromedriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import url
import logging

# imposta -2 ore rispetto all'ora locale
ORA = 8
MINUTI = 49



slot = ["UC_FreeFitness_GVPeriodi_CBScelta_0","UC_FreeFitness_GVPeriodi_CBScelta_1","UC_FreeFitness_GVPeriodi_CBScelta_2","UC_FreeFitness_GVPeriodi_CBScelta_3"]

def prenotazione(data, orario, username, password):
    # chrome_driver = ChromeDriverManager().install()
    # driver = Chrome(service=Service(chrome_driver))
    
    chrome_driver = "/usr/bin/chromedriver"
    from selenium.webdriver.chrome.options import Options
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/chromium-browser"
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")
    driver = Chrome(service=Service(chrome_driver), options=chrome_options)

    try:
        driver.get(url)
        logging.info("Apertura del sito web in corso...")

        # Login
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "UC_FreeFitness_TXTUsername"))
        )
        driver.find_element(By.ID, "UC_FreeFitness_TXTUsername").send_keys(username)
        logging.info("Username inserito.")
        driver.find_element(By.ID, "UC_FreeFitness_TXTPassword").send_keys(password)
        logging.info("Password inserita.")
        driver.find_element(By.ID, "UC_FreeFitness_BTNLogin").click()
        logging.info("Login in corso...")
        
        # Calcola il tempo da attendere fino al target (TARGET_HOUR e TARGET_MINUTE)
        from datetime import datetime, timedelta
        import time
        now = datetime.now()
        target_time = now.replace(hour=ORA, minute=MINUTI, second=0, microsecond=0)
        if now >= target_time:
            target_time += timedelta(days=1)
        wait_seconds = (target_time - now).total_seconds()
        print(f"Login completato. Attendo {wait_seconds:.0f} secondi fino al target: {target_time}")
        time.sleep(wait_seconds)
        
        # element = driver.find_element(By.ID, "UC_FreeFitness_HFTotalePrenotazioniSettimana")
        # driver.execute_script(f"arguments[0].setAttribute('value', '1')", element) 
        # print("Impostato il valore prenotazioni effettuate settimana a 1")  
        # input("Premi invio per continuare...")
        
        # element = driver.find_element(By.ID, "UC_FreeFitness_HFOrePrenotabilisettimana")
        # driver.execute_script(f"arguments[0].setAttribute('value', '3')", element) 
        # print("Impostato il valore ora a settimana a 3")  
        # input("Premi invio per continuare...")
        
        # element = driver.find_element(By.ID, "UC_FreeFitness_HFOrePrenotabiliGiorno")
        # driver.execute_script(f"arguments[0].setAttribute('value', '2')", element) 
        # print("Impostato il valore prenotazioni giorno a 2")  
        # input("Premi invio per continuare...")
        
        driver.implicitly_wait(1)
        title = f"{data}"
        xpath = f"//a[@title='{title}']"
        driver.find_element(By.XPATH, xpath).click()
        logging.info(f"Data selezionata: {data}")

        driver.implicitly_wait(0.6)
        
        
        
        # element = driver.find_element(By.ID, slot[orario])
        # driver.execute_script("arguments[0].removeAttribute('disabled');", element)
        # print("Rimosso l'attributo disabled da checkbox")  
        # input("Premi invio per continuare...")
        
        driver.find_element(By.ID, slot[orario]).click()
        print("Checkbox selezionata")
        # input("Premi invio per continuare...")
        driver.find_element(By.ID, "UC_FreeFitness_LBConferma").click()
        logging.info(f"Orario selezionato: {slot[orario]}")
        
        try:
            # Aspetta fino a 10 secondi affinché compaia l'elemento, normalizzando gli spazi
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h2[normalize-space(text())='Prenotazione effettuata con successo']"))
            )
            logging.info("Prenotazione effettuata con successo.")
            print("Successo")
            return 1
        except TimeoutException:
            logging.error("Timeout: messaggio di successo non trovato entro 10 secondi")
            print("Insuccesso: messaggio di successo non trovato entro 10 secondi")
            return 0
        except NoSuchElementException:
            logging.error("Elemento non trovato: messaggio di successo non trovato")
            print("Insuccesso")
            return 0
    except Exception as e:
        logging.error(f"Errore durante la prenotazione: {e}")
        print("Errore generico:", e)
        return 0

    finally:
        # Chiudi il browser
        logging.info("Chiusura del browser...")
        driver.quit()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Debug prenotazione function")
    parser.add_argument("--hour", type=int,   required=False, default=ORA,    help="Hour for booking (0–23)")
    parser.add_argument("--minute", type=int, required=False, default=MINUTI, help="Minute for booking (0–59)")
    args = parser.parse_args()
    
    # Override module-level booking time
    ORA    = args.hour
    MINUTI = args.minute

    data = "15 maggio"
    slot = 0
    username = "s325040@studenti.polito.it"
    password = "XZdVoop0yW8zwuX"
    result = prenotazione(data,slot,username,password)
    if result == 1:
        print("Prenotazione riuscita")
    else:
        print("Prenotazione non riuscita")