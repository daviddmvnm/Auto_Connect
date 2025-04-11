import time
import random
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By


def human_sleep(base=2, variance=1):
    delay = max(0, random.uniform(base - variance, base + variance))
    time.sleep(delay)

def human_scroll(driver, total_scrolls=5):
    for _ in range(total_scrolls):
        scroll_amount = random.randint(300, 900)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        human_sleep(1, 0.5)

def random_hover(driver, selector="a"):
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        if elements:
            el = random.choice(elements)
            ActionChains(driver).move_to_element(el).perform()
            human_sleep(1, 0.3)
    except Exception:
        pass

def take_linkedin_detour(driver):
    import random
    from time import sleep

    destinations = [
        ("https://www.linkedin.com/feed/", "Feed"),
        ("https://www.linkedin.com/mynetwork/", "My Network"),
        ("https://www.linkedin.com/jobs/", "Jobs"),
        ("https://www.linkedin.com/notifications/", "Notifications"),
    ]
    url, label = random.choice(destinations)

    print(f"\n[Detour] Visiting {label} page...")
    driver.get(url)
    human_sleep(3.5, 1.5)

    human_scroll(driver, total_scrolls=random.randint(2, 4))
    random_hover(driver, "a")
    human_sleep(1.5, 0.7)

def force_stabilize_view(driver, down_scrolls=5):
    for _ in range(down_scrolls):
        driver.execute_script("window.scrollBy(0, window.innerHeight / 2);")
        time.sleep(random.uniform(0.4, 0.7))
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(random.uniform(1.5, 2.5))
