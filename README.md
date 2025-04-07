#  AutoConnect

**AutoConnect** is a Python-powered desktop automation tool that looks to smartly automate cold LinkedIn outreach.

It scrapes profiles, predicts who’s most likely to accept a connection using a simple machine learning model, and sends smart, human-like invites — all via a clean, one-click GUI.

---

##  Features

**Modular pipeline** — `scrape → parse → tag → predict → connect`  
**Selenium scraping** that mimics real human behavior  
**ML-powered predictions** (scikit-learn logistic model)  
**Invite & acceptance tracking** built in  **Fully configurable** via `config.json` (interests, thresholds, model path)  
**Train new models** easily with built-in tooling  
**Simple GUI** (tkinter) with one-click control of the entire pipeline  

---

## Linux First, but Flexible

- Built and tested on Ubuntu-based Linux systems
- Bundled as a self-contained executable using PyInstaller
- Just click or run it from terminal to launch the GUI
- ⚠ For now, Linux only — Windows `.exe` coming later

---

##  How to Use

1. **Edit your targeting preferences** in `config.json`  
2. **Launch the GUI** (click the bundled app or run `python main.py`)  
3. **Scrape profiles** and let the bot tag + score them  
4. **Send invites** manually or automatically  
5. **Track results** with built-in invite/acceptance metrics  

---

## Preview
![image](https://github.com/user-attachments/assets/a39dd3a0-dae6-44f9-8fef-df6f47326050)

