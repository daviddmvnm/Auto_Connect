# 🕸AutoConnect – ML-Powered Outreach Tool

**AutoConnect** is a Python-based desktop tool for automating cold LinkedIn outreach.

It scrapes profiles, predicts who’s most likely to accept a connection using a basic ML model, and sends invites — all controlled through a simple GUI.

This is an end-to-end prototype: scraping, feature engineering, modeling, automation, GUI, and bundling as a Linux AppImage.

> It's my first project like this — leaving behind Jupyter notebooks and gluing everything together into a real, working app.  
> It's not perfect, but the core functionality works. Consider this a rough MVP, so enjoy? 

---

## ⚠️ Disclaimer

This tool automates LinkedIn activity.  
Use at your own risk.  
It likely violates LinkedIn’s Terms of Service.  
I built this for learning purposes only — not as a production tool.

---

## Features

- Persistent sessions using cookie extraction  
- Undetected scraping of LinkedIn profiles  
- HTML parsing and feature extraction  
- Hypothesis-based feature engineering  
- Logistic regression model to predict connection acceptance  
- Auto-send connection requests to top-ranked profiles  
- Invite tracking and acceptance rate logging  
- Simple GUI built with `tkinter`  

---

## Tech Stack

- Python (Selenium, BeautifulSoup, Scikit-learn, Tkinter)  
- Undetected ChromeDriver  
- SQLite for storage  
- PyInstaller to bundle as `.AppImage`  

---

## Install (Linux Only 🐧)

Tested on Ubuntu 22.04.

### 1. Download the AppImage

- [Download from GitHub Releases](https://github.com/daviddmvnm/Auto_Connect/releases/tag/v0.1.1%28APP-IMAGE%29)  
or use:

```bash
wget https://github.com/daviddmvnm/Auto_Connect/releases/download/v0.1.1%28APP-IMAGE%29/AutoConnect-x86_64.AppImage -O AutoConnect.AppImage
```

### 2. Make it executable
```bash
chmod +x AutoConnect.AppImage
```

### 3. Run it
```bash
./AutoConnect.AppImage
```
Or just double-click.

---

## More Info

I wrote about how I built this here:  
[Build Notes – Google Doc](https://docs.google.com/document/d/1a6fNa6ATkD4cw9ORhz8tiGCtCSGLhGDziHp_gkv7sYc/edit?tab=t.khzo1efbhjtw)

---

## GUI Preview

![image](https://github.com/user-attachments/assets/16994228-8779-4d2f-950c-1d60097589ea)

---

## Contact 👋

If you want to give feedback, ask questions, etc, message me directly I'm up for a chat 
