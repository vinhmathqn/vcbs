# Converted from Jupyter Notebook to Python script
# Note:
# - Removed Jupyter/IPython magics and shell commands.
# - Ensure all required libraries are installed before running in GitHub Actions.
# ===== Cell 1 =====
# library
import numpy as np
import time
import pytz
from lxml import html
from bs4 import BeautifulSoup, Tag
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as chrome_options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

# ===== Cell 2 =====
# utility function
def get_date_time():
    tz = pytz.timezone('Asia/Ho_Chi_Minh')
    t = datetime.now(tz)
    return int(t.strftime('%Y%m%d')), t.hour * 100 + t.minute

def build_DCOL(COL):
    DCOL, n = {}, len(COL)
    for i in range(n):
        DCOL[COL[i]] = i
    return DCOL

def vstack_row(arr, row, pgdn=True):
    result = None
    if arr is None:
        result = np.array([row])
    else:
        result = np.vstack([arr, row]) if pgdn == True else np.vstack([row, arr])
    return result

def get_vcbs_const():
    DT, NUM = {}, []
    EXCH = ['hose', 'hnx']
    XP = [['//*[@id="HOSE_Group"]/a/span', '//*[@id="tab4"]/p'], ['//*[@id="HNX_Group"]/a/span', '//*[@id="tab7"]/p'], \
         ['//*[@id="HOSE_Group"]/a/span', '//*[@id="tab6"]/p'], ['//*[@id="HNX_Group"]/a/span', '//*[@id="tab9"]/p']]
    url = "https://priceboard.vcbs.com.vn/Priceboard#"
    opt = chrome_options()
    opt.add_argument("--headless")
    driver = webdriver.Chrome(opt)
    wait = WebDriverWait(driver, 10)
    driver.get(url)
    for i in range(len(EXCH)):
        exch, xp1, xp2 = EXCH[i], XP[i][0], XP[i][1]
        time.sleep(5)
        parent = wait.until(EC.presence_of_element_located((By.XPATH, xp1)))
        ActionChains(driver).move_to_element(parent).perform()
        child = wait.until(EC.presence_of_element_located((By.XPATH, xp2)))
        child = wait.until(EC.element_to_be_clickable((By.XPATH, xp2)))
        child.click()
        time.sleep(5)
        num = len(driver.find_elements(By.XPATH, '//*[@id="priceboardContentTableBody"]/tr'))
        L = XP[i] + [num]
        DT[exch] = L
    return DT

# ===== Cell 3 =====
# core functions
def search_vcbs(driver, exch):
    DT = vcbs_const
    xp = '//*[@id="priceboardContentTableBody"]'
    xp1, xp2 = DT[exch][0], DT[exch][1]
    wait = WebDriverWait(driver, 10)
    parent = wait.until(EC.presence_of_element_located((By.XPATH, xp1)))
    ActionChains(driver).move_to_element(parent).perform()
    child = wait.until(EC.presence_of_element_located((By.XPATH, xp2)))
    child = wait.until(EC.element_to_be_clickable((By.XPATH, xp2)))
    child.click()
    wait.until(EC.presence_of_element_located((By.XPATH, xp)))
    wait.until(EC.visibility_of_element_located((By.XPATH, xp)))
    wait.until(lambda driver: len(driver.find_elements(By.XPATH, '//*[@id="priceboardContentTableBody"]/tr')) >= DT[exch][2])

def get_html(driver, xp):
    html = driver.find_element(By.XPATH, xp)
    return html.get_attribute('innerHTML')

def build_row_vcbs(date, exch, stk, block):
    def get_value(block, stk, id):
        td = block.find('td', id=f"{stk}{id}")
        value = np.nan
        if td:
            try:
                value = td.text.strip()
                value = float(value.replace(',', ''))
            except:
                pass
        return value
    row = [date, exch, stk]
    ID = ['ceiling', 'floor', 'priorClosePrice', 'best3Bid', 'best3BidVolume', 'best2Bid', 'best2BidVolume', 'best1Bid', 'best1BidVolume', \
      'change2', 'closePrice', 'closeVolume', 'best1Offer', 'best1OfferVolume', 'best2Offer', 'best2OfferVolume', \
      'best3Offer', 'best3OfferVolume', 'totalTrading', 'open', 'high', 'low', 'foreignBuy', 'foreignSell', 'foreignRemain']
    for id in ID:
        value = get_value(block, stk, id)
        row.append(value)
    return row

def collect_exch_vcbs(driver, exch):
    date, tm = get_date_time()
    count, xp = 0, '//*[@id="priceboardContentTableBody"]'
    while count <= 3:
        try:
            search_vcbs(driver, exch)
            content = get_html(driver, xp)
            break
        except:
            count += 1
    if count == 4:
        return None
    DATA, soup = None, BeautifulSoup(content, 'html.parser')
    BLOCK = soup.find_all('tr')
    for block in BLOCK:
        if block.has_attr('name'):
            stk = block['name']
            if stk != 's_8_s':
                row = build_row_vcbs(date, exch, stk, block)
                DATA = vstack_row(DATA, row)
    return DATA

# ===== Cell 4 =====
# constants
COL_vcbsr = ['date', 'exch', 'stk', 'ceil', 'floor', 'adj', 'b3', 'nshb3', 'b2', 'nshb2', 'b1', 'nshb1', 'chng2', 'cls', 'nshcls', \
                's1', 'nshs1', 's2', 'nshs2', 's3', 'nshs3', 'nsh', 'opn', 'high', 'low', 'Fb', 'Fs', 'Fh']
Dvcbsr = build_DCOL(COL_vcbsr)
vcbs_const = get_vcbs_const()
count = 0

# ===== Cell 5 =====
# main
while count <= 5:
    count += 1
    try:
        url = "https://priceboard.vcbs.com.vn/Priceboard#"
        opt = chrome_options()
        opt.add_argument("--headless")
        driver = webdriver.Chrome(opt)
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        wait.until(lambda driver: len(driver.find_elements(By.XPATH, '//*[@id="priceboardContentTableBody"]/tr')) >= vcbs_const['hose'][2])
        Dc = Dvcbsr
        DATA, flag = None, True
        for exch in ['hose', 'hnx']:
            ARR = collect_exch_vcbs(driver, exch)
            if ARR is None:
                flag = False
            DATA = ARR if DATA is None else np.vstack((DATA, ARR))
        if flag == True:
            dt, tm = get_date_time()
            yr = dt // 10000
            path = f"data/{yr}"
            os.makedirs(path, exist_ok=True)
            np.save(f"{path}/{dt}.npy", DATA)
            break
    except:
        pass
