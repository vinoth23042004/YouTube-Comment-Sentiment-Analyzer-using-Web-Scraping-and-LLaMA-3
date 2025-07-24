
# 🎬 YouTube Comment Sentiment Analyzer using Web Scraping and LLaMA-3

A Streamlit-based web app that:
- Extracts YouTube video comments
- Translates them to English (if needed)
- Analyzes emotional sentiment using NVIDIA's LLaMA 3.1-8B API
- Displays sentiment results with interactive charts

---

### 🎥 Video Demo

[![Watch Demo on YouTube](https://img.youtube.com/vi/T1tlS-k4OuI/0.jpg)](https://youtu.be/T1tlS-k4OuI?si=NxHydT_Et8mSBlbQ)

### 🖼️ Screenshots

![Sample Screenshot 1](https://raw.githubusercontent.com/vinoth23042004/YouTube-Comment-Sentiment-Analyzer-using-Web-Scraping-and-LLaMA-3/main/assests/sample_1.jpg)

![Sample Screenshot 2](https://raw.githubusercontent.com/vinoth23042004/YouTube-Comment-Sentiment-Analyzer-using-Web-Scraping-and-LLaMA-3/main/assests/sample_2.png)

---

## 🚀 How to Run

### 1. Clone or Download This Repository

```bash
git clone <your-repo-url>
cd <your-folder-name>
```

### 2. Install Required Dependencies

```bash
pip install -r requirements.txt
```

You’ll need:
- `streamlit`
- `selenium`
- `pandas`
- `plotly`
- `requests`
- `openai`
- `webdriver-manager`

### 3. Replace the API Key

➡️ **Generate your NVIDIA API key from:**  
[https://build.nvidia.com/meta/llama-3_1-8b-instruct](https://build.nvidia.com/meta/llama-3_1-8b-instruct)

Login and copy your API key. Replace the default value inside `app.py` with your personal key:
```python
api_key = st.text_input("NVIDIA API Key", type="password", value="your-api-key-here")
```

---

## 💻 Launch the App

```bash
streamlit run app.py
```

---

## 📋 Features

- ✅ Comment extraction from YouTube
- 🌍 Auto translation to English using Google Translate API
- 🧠 Sentiment analysis using NVIDIA LLaMA 3.1
- 📈 Real-time visualization of results
- 🧹 Temporary file cleanup after processing

---

## 📂 File Structure

```bash
.
├── app.py                # Main Streamlit application
├── comments.txt          # Temporary file storing raw YouTube comments
├── translated.txt        # Translated comments
├── result.txt            # Final sentiment results
├── requirements.txt      # Required Python libraries
```

---

## 📌 Notes

- Ensure Chrome browser is installed (used by Selenium).
- Works best for public YouTube videos with visible comments.
- Use your own API key from the official NVIDIA link above.


