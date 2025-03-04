# 🏠 Funda_Scraper

**Funda_Scraper** is your go-to tool for scraping housing data from **Funda**, the Dutch real estate platform.

---

### ⚠️ Important Notes

- **Personal Use Only**: Scraping Funda is permitted **only for personal use**, as outlined in Funda's Terms and Conditions.
- **No Commercial Use**: Any commercial use of this package is strictly prohibited.
- **Disclaimer**: The author is not liable for any misuse of this tool. Use it responsibly!

---

## ✨ Features

- **Asynchronous Programming with asyncio**:
  - Leverages Python's async capabilities for lightning-fast data collection.
  - Runs multiple web requests concurrently instead of waiting for each request to complete.
  - Significantly reduces total scraping time compared to traditional sequential approaches.

- **Stealthy Scraping with curl_cffi**:
  - Bypasses basic web scraping detection mechanisms.
  - Provides a more robust way to fetch data without triggering anti-scraping protections.

- **Flexible Batch Processing**:
  - Control the number of ads processed simultaneously.
  - Fine-tune performance vs. risk of IP blocking.

User-Friendly Features:
- Automatic progress saving.
- Intuitive graphical interface.
- Seamless pause and resume functionality.

---

## 🛠️ Installation

**Clone the repository**:
````
git clone https://github.com/YoussefBJemia/Funda_scraper
cd Funda_scraper
pip install -r requirements.txt
python main.py
````

---

## 🚀 Usage

1. **Start Scraping**:
   Run the main script to begin scraping:
   ````
   python main.py
   ````
   This will launch the Graphical User Interface (GUI).

   ![Interface Screenshot](Img/interface.PNG)
2. **Start Scraping**

Click the **"Start Scraping"** button in the GUI to begin the process.

The scraper will start running, and you can monitor its progress in the terminal or command line.

![Running Code Screenshot](Img/progress.PNG) <!-- Replace with actual path -->

3. **Resumable Scraping**

- Ads are saved automatically whenever a neighborhood is fully processed.
- If the program is stopped, it can resume from where it left off, ensuring no data is lost.

![Resume GUI Screenshot](Img/continue.PNG) <!-- Replace with actual path -->
