# 🏠 Funda_Scraper

**Funda_Scraper** is your go-to tool for scraping housing data from **Funda**, the Dutch real estate platform. Whether you're looking for properties **for sale** or **for rent**, or exploring historical housing trends from the past few years, Funda_Scraper makes it simple and (hopefully) efficient.

---

### ⚠️ Important Notes

- **Personal Use Only**: Scraping Funda is permitted **only for personal use**, as outlined in Funda's Terms and Conditions.
- **No Commercial Use**: Any commercial use of this package is strictly prohibited.
- **Disclaimer**: The author is not liable for any misuse of this tool. Use it responsibly!

---

## ✨ Features

- **Asynchronous Scraping**: Utilizes `asyncio` for high-performance, concurrent web requests, combined with `curl_cffi` for undetected scraping.
- **Scraping by Batch**: Control how many ads are processed at once by adjusting `self.batch_processing_size` in `Scraper/config.py`. Increase the number for faster scraping, but be cautious—larger batches may increase the risk of your IP getting blocked.
- **User-Friendly Interface**: An intuitive interface within the code for easy configuration and execution.

---

## 🛠️ Installation

1. **Clone the repository**:
````git clone https://github.com/YoussefBJemia/Funda_scraper
cd Funda_scraper
pip install -r requirements.txt
python Funda_scraper/main.py````