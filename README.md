# **AutoConnect prototype**

**AutoConnect** is a Python-based automation tool that helps streamline cold LinkedIn outreach. Built as a desktop prototype, it scrapes profiles, predicts who’s most likely to accept a connection request using a simple machine learning model, and sends invites — all through a clean GUI.

This project explores behavioral patterns in online networking and turns them into a fully working ML-powered bot. It’s my first end-to-end system: scraping, feature engineering, modeling, GUI design, and bundling as a standalone executable

---
# **Quick Disclaimer!!!**
**Hey — I'm a student, I built this to learn and mess around with automation.
Yes, it does technically work. Yes, it can automate parts of LinkedIn.
No, this is not me telling you to go break LinkedIn’s Terms of Service.**

Use it at your own risk. If you get banned, that’s on you.
This was made for fun, education, and a bit of desperation in the job hunt.
---

## Features

- Scrape LinkedIn profiles via undetected browser automation
- Parse and extract structured data from raw HTML
- Engineer hypothesis-based features
- Train or load a logistic regression model to predict acceptance likelihood
- Send automated connection requests to top-ranked profiles
- Track invites, responses, and acceptance rates
- Control scraping and outreach from a tkinter GUI

---

## Technologies Used

- Python (Selenium, BeautifulSoup, scikit-learn, tkinter)
- Undetected ChromeDriver for stealth automation
- SQLite for persistent tracking
- PyInstaller for bundling into a standalone app

---

## Notes

- The bundled version is Linux-only for now (tested on Ubuntu 22.04)
- Requires an initial login and then saves your li_at cookie to be injected until it expires
- All behavior is partially randomised and human-like to avoid detection
- This prototype was built as part of an assignment for a uni datascience module

---

## How to Try It?
1. 
 - A standalone executable is available in the [Releases](https://github.com/daviddmvnm/Auto_Connect/releases) tab.  
 - Drop it in a folder
 - navigate to the folder and run `chmod +x AutoConnectv1` to make it exectuable, if you dont do this it can't run
 - run it, and follow the built-in tracker and config system.
2.
 -It will also work just by running main.py, but to do this you will have to use the requirements.txt to create an appropriate environment
 -This will lead to some challenges for most people as the project uses an older python version 3.10.12 for libararies like undectedchromedriver to work

# Preview 
![image](https://github.com/user-attachments/assets/ba5d6068-2c6d-4408-a46f-7cb9156ae2de)

