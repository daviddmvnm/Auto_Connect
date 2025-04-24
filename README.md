# 🕸️ **AutoConnect – ML-Powered Outreach Tool**

**AutoConnect** is a Python-based desktop app for automating cold LinkedIn outreach.

It scrapes profiles, predicts who’s most likely to accept a connection using a basic ML model, and sends invites — all controlled through a simple GUI.

This is a full end-to-end prototype: scraping, feature engineering, modeling, automation, GUI, and bundling as a Linux AppImage.

>*🛠️ My first project like this | leaving behind Jupyter notebooks and gluing everything together into a real, working app. It's not perfect, but the core functionality works. Consider this a rough MVP, so enjoy?*

 >*🎯 This was my capstone after 6 months of making a serious effort to learn data science | not just models, but the full stack: scraping, feature engineering, automation, and deployment as a real tool any feedback is massively appreciated.*

---

## ⚠️ **Disclaimer**

This tool automates LinkedIn activity.  
**Use at your own risk.**  
It likely violates LinkedIn’s Terms of Service.  
I built this purely for learning purposes — **not for production use.**

---

## 📂 **Project Structure**

```
AutoConnect/
├── Pipeline/               # Core logic: scraping, parsing, feature engineering, ML model training
├── images/                 # GUI assets (icons, logos)
├── models/                 # Saved ML models (e.g., logistic_model.joblib)
├── .gitignore              # Git tracking rules (ignores cache, compiled files, etc.)
├── AutoConnect.spec        # PyInstaller spec file for building the AppImage
├── README.md               # Project overview, install instructions, usage guide
├── blog_build story.pdf    # Data-driven blog write-up (submitted for the empirical project)
├── config.json             # Editable configuration file (max invites, model choice, interest keywords)
├── main.py                 # GUI launcher and main app entry point
├── manual.txt              # User manual included with the app
├── pipeline_entrypoint.py  # Command-line entry point for triggering pipeline stages without the GUI
├── requirements.txt        # Python package dependencies for development and reproducibility
```

✅ **Notes on Key Files:**
- **`main.py`**: The main executable Python script that launches the GUI.
- **`pipeline_entrypoint.py`**: Allows running the scraping, parsing, and model prediction pipeline outside the GUI.
- **`config.json`**: Controls bot behavior (invite limits, keywords, model selection). Now uses a persistent user-writable config system.
- **`AutoConnect.spec`**: Defines how the app is bundled into a portable Linux binary using PyInstaller

## 🚀 **Features**

✅ Persistent sessions using cookie extraction  
✅ Undetected scraping of LinkedIn profiles  
✅ HTML parsing and feature extraction  
✅ Hypothesis-based feature engineering  
✅ Logistic regression model to predict connection acceptance  
✅ Auto-send connection requests to top-ranked profiles  
✅ Invite tracking and acceptance rate logging  
✅ Simple GUI built with `tkinter`  

---

## 🧰 **Tech Stack**

- **Python:** Selenium, BeautifulSoup, scikit-learn, Tkinter  
- **Browser Automation:** Undetected ChromeDriver  
- **Database:** SQLite for storage  
- **Bundling:** PyInstaller → Linux `.AppImage`

---

## 🐧 **Install (Linux Only)**

Tested on **Ubuntu 22.04**.

### 1️⃣ Download the AppImage

- [Download from GitHub Releases](https://github.com/daviddmvnm/Auto_Connect/releases/tag/v0.1.1%28APP-IMAGE%29)  
_or use `wget`:_

```bash
wget "https://github.com/daviddmvnm/Auto_Connect/releases/download/v0.1.1%28APP-IMAGE%29/AutoConnect.x86_64.AppImage" -O AutoConnect.AppImage
```

---

### 2️⃣ Make it executable:

```bash
chmod +x AutoConnect.AppImage
```

---

### 3️⃣ Run the app:

```bash
./AutoConnect.AppImage
```

_or just double-click the file — whatever floats your boat._

---

### 🗑️ Uninstall:

```bash
rm AutoConnect.AppImage
```

---

## 📄 **More Info**

📝 I wrote about how I built this here:  
[**Build Notes – Google Doc**](https://docs.google.com/document/d/15pBLOmaXcsLjkpP-OE33zfwmCYpWrEhTrZ1tFP6JGuo/edit?tab=t.khzo1efbhjtw#heading=h.p9jatc3v45hz)

---

## 🖥️ **GUI Preview**

![image](https://github.com/user-attachments/assets/16994228-8779-4d2f-950c-1d60097589ea)

---

## 👋 **Contact**

If you want to give feedback, ask questions, or just chat — feel free to reach out!

Also add me on linkedin... [**LinkedIn**](https://www.linkedin.com/in/david-clements442/)
