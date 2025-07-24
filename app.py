import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
import subprocess
import time
import re
from datetime import datetime
import tempfile
import shutil

# Import your existing modules
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import random
import requests
from urllib.parse import quote
from openai import OpenAI
import json

# Set page config
st.set_page_config(
    page_title="YouTube Comment Sentiment Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #FF6B6B;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    .section-header {
        color: #4ECDC4;
        font-size: 1.5rem;
        font-weight: bold;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #000080;
        border: 1px solid #bee5eb;
        border-radius: 0.25rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class YouTubeCommentExtractor:
    def __init__(self, video_url):
        self.video_url = video_url
        
    def remove_emojis(self, text):
        emoji_pattern = re.compile("["
                                  u"\U0001F600-\U0001F64F"  # emoticons
                                  u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                  u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                  u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                  u"\U00002702-\U000027B0"
                                  u"\U000024C2-\U0001F251"
                                  u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                                  u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
                                  u"\U00002600-\U000026FF"  # Miscellaneous Symbols
                                  u"\U00002700-\U000027BF"  # Dingbats
                                  "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', text)
    
    def extract_comments(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = None
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get(self.video_url)
            time.sleep(5)
            
            # Scroll to load comments
            driver.execute_script("window.scrollTo(0, 800);")
            time.sleep(3)
            
            # Load all comments
            last_height = driver.execute_script("return document.documentElement.scrollHeight")
            scroll_pause_time = 2
            
            while True:
                driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                time.sleep(scroll_pause_time)
                new_height = driver.execute_script("return document.documentElement.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # Extract comments
            comments = driver.find_elements(By.XPATH, '//*[@id="content-text"]')
            
            all_comments = []
            for c in comments:
                comment_text = c.text.strip()
                if comment_text != "":
                    clean_comment = self.remove_emojis(comment_text).strip()
                    if clean_comment != "":
                        all_comments.append(clean_comment)
            
            # Skip first comment (usually video description)
            actual_comments = all_comments[1:] if len(all_comments) > 1 else all_comments
            
            # Save to file
            with open('comments.txt', 'w', encoding='utf-8') as file:
                for i, comment in enumerate(actual_comments, 1):
                    file.write(f"Comment {i}:\n")
                    file.write(f"Original: {comment}\n")
                    file.write("-" * 80 + "\n")
                    if i < len(actual_comments):
                        file.write("\n")
            
            return len(actual_comments)
            
        except Exception as e:
            raise Exception(f"Error extracting comments: {e}")
        finally:
            if driver:
                driver.quit()

class CommentTranslator:
    def __init__(self):
        pass
    
    def translate_with_requests_api(self, text):
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                'client': 'gtx',
                'sl': 'auto',
                'tl': 'en',
                'dt': 't',
                'q': text
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result and result[0] and result[0][0]:
                    translated_text = result[0][0][0]
                    return translated_text
        except Exception as e:
            pass
        return None
    
    def extract_translated_text(self, file_path):
        translated_texts = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            sections = content.split('--------------------------------------------------------------------------------')
            
            for i, section in enumerate(sections):
                if section.strip():
                    lines = section.strip().split('\n')
                    for line in lines:
                        if line.strip().startswith('Original:'):
                            translated_text = line.strip().split('Original:', 1)[1].strip()
                            if translated_text:
                                translated_texts.append({
                                    'index': i + 1,
                                    'text': translated_text
                                })
                            break
            
            return translated_texts
        except Exception as e:
            raise Exception(f"Error reading comments file: {e}")
    
    def translate_comments(self):
        translated_texts = self.extract_translated_text('comments.txt')
        
        if not translated_texts:
            raise Exception("No comments found to translate")
        
        enhanced_results = []
        
        for item in translated_texts:
            # Try translation
            enhanced_text = self.translate_with_requests_api(item['text'])
            if not enhanced_text:
                enhanced_text = item['text']  # Keep original if translation fails
            
            enhanced_results.append({
                'index': item['index'],
                'original_translated': item['text'],
                'enhanced': enhanced_text
            })
        
        # Save results
        with open('translated.txt', 'w', encoding='utf-8') as f:
            f.write("=== Enhanced Translation Results (Anti-Detection Version) ===\n\n")
            f.write(f"Total Items Processed: {len(enhanced_results)}\n")
            f.write(f"Processing Method: API + Stealth Browser Fallback\n\n")
            
            for result in enhanced_results:
                f.write(f"{result['index']}.\n")
                f.write(f"Original Translation: {result['original_translated']}\n")
                f.write(f"Enhanced (English): {result['enhanced']}\n")
                f.write("-" * 80 + "\n")
        
        return len(enhanced_results)

class SentimentAnalyzer:
    def __init__(self, api_key):
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key,
        )
    
    def _get_completion(self, prompt, temperature=0.1, max_retries=3):
        for attempt in range(max_retries):
            try:
                completion = self.client.chat.completions.create(
                    model="meta/llama-3.1-8b-instruct",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    top_p=0.7,
                    max_tokens=512,
                    stream=False
                )
                response = completion.choices[0].message.content
                return response
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return "Error"
    
    def analyze_sentiment(self, text):
        prompt = f"""
Analyze the SENTIMENT of this text - meaning the emotional tone expressed in the words.

Focus on:
- The actual words chosen (positive, negative, neutral)
- Emotional indicators in the language
- Intensity of the sentiment expressed
- Overall tone and feeling conveyed

TEXT: "{text}"

Classify the sentiment as:
- Positive: Expresses satisfaction, happiness, approval, gratitude, or other positive emotions
- Negative: Expresses dissatisfaction, anger, disappointment, frustration, or other negative emotions  
- Neutral: Factual, balanced, or lacks clear emotional indicators

ANSWER FORMAT:
Sentiment: [Positive/Negative/Neutral]
Confidence: [0-100]%
Key_Words: [Words that indicate this sentiment]
Reasoning: [Brief explanation of why]
"""
        
        response = self._get_completion(prompt)
        return self._parse_sentiment_response(response)
    
    def _parse_sentiment_response(self, response):
        result = {
            'sentiment': 'Error',
            'confidence': 50,
            'key_words': 'None identified',
            'reasoning': 'No reasoning provided'
        }
        
        if not response or response == "Error":
            return result
        
        response_lower = response.lower()
        if 'positive' in response_lower:
            result['sentiment'] = 'Positive'
        elif 'negative' in response_lower:
            result['sentiment'] = 'Negative'
        elif 'neutral' in response_lower:
            result['sentiment'] = 'Neutral'
        
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('Sentiment:'):
                sentiment = line.split(':', 1)[1].strip()
                if sentiment in ['Positive', 'Negative', 'Neutral']:
                    result['sentiment'] = sentiment
            elif line.startswith('Confidence:'):
                conf_str = re.findall(r'\d+', line)
                result['confidence'] = int(conf_str[0]) if conf_str else 50
            elif line.startswith('Key_Words:'):
                result['key_words'] = line.split(':', 1)[1].strip()
            elif line.startswith('Reasoning:'):
                result['reasoning'] = line.split(':', 1)[1].strip()
        
        return result
    
    def parse_translation_file(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
            
            statements = []
            lines = content.split('\n')
            
            for line in lines:
                if line.strip().startswith('Enhanced (English):'):
                    statement = line.split('Enhanced (English):', 1)[1].strip()
                    if statement:
                        statements.append(statement)
            
            return statements
        except Exception as e:
            raise Exception(f"Error reading translation file: {e}")
    
    def analyze_comments(self):
        statements = self.parse_translation_file('translated.txt')
        if not statements:
            raise Exception("No translated comments found")
        
        sentiment_counts = {
            'Positive': 0,
            'Negative': 0,
            'Neutral': 0
        }
        
        results = []
        
        for i, statement in enumerate(statements, 1):
            analysis = self.analyze_sentiment(statement)
            
            if analysis['sentiment'] != 'Error':
                sentiment_counts[analysis['sentiment']] += 1
                
                result_entry = {
                    'statement_number': i,
                    'text': statement,
                    'overall_sentiment': analysis['sentiment'],
                    'confidence': analysis['confidence'],
                    'key_words': analysis['key_words'],
                    'reasoning': analysis['reasoning']
                }
                results.append(result_entry)
        
        # Save results
        with open('result.txt', 'w', encoding='utf-8') as file:
            file.write("="*80 + "\n")
            file.write("SENTIMENT ANALYSIS RESULTS\n")
            file.write("="*80 + "\n")
            file.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            file.write(f"Total Statements: {len(results)}\n\n")
            
            file.write("SENTIMENT DISTRIBUTION SUMMARY:\n")
            file.write("-" * 40 + "\n")
            file.write(f"Positive Sentiment: {sentiment_counts['Positive']}\n")
            file.write(f"Negative Sentiment: {sentiment_counts['Negative']}\n")
            file.write(f"Neutral Sentiment: {sentiment_counts['Neutral']}\n")
            file.write("\n" + "="*80 + "\n")
            file.write("DETAILED RESULTS:\n")
            file.write("="*80 + "\n\n")
            
            for result in results:
                file.write(f"Statement {result['statement_number']}:\n")
                file.write(f"Text: \"{result['text']}\"\n")
                file.write(f"Overall Sentiment: {result['overall_sentiment']}\n")
                file.write(f"Confidence: {result['confidence']}%\n")
                file.write(f"Key Words: {result['key_words']}\n")
                file.write(f"Logic Applied: Direct sentiment analysis - {result['overall_sentiment']} sentiment detected\n")
                file.write("-" * 80 + "\n\n")
        
        return results, sentiment_counts

def cleanup_files():
    """Delete all temporary files"""
    files_to_delete = ['comments.txt', 'translated.txt', 'result.txt']
    for file in files_to_delete:
        try:
            if os.path.exists(file):
                os.remove(file)
        except:
            pass

def main():
    # Header
    st.markdown('<div class="main-header">📊 YouTube Comment Sentiment Analyzer</div>', unsafe_allow_html=True)
    
    # Sidebar for API key
    with st.sidebar:
        st.header("⚙️ Configuration")
        api_key = st.text_input("NVIDIA API Key", type="password", value="your-api-key-here")
        st.info("💡 Enter your NVIDIA API key for sentiment analysis")
        
        st.header("📋 Process Steps")
        st.write("1. 🎬 Extract YouTube comments")
        st.write("2. 🌐 Translate to English")
        st.write("3. 🎭 Analyze sentiment")
        st.write("4. 📊 Display results")
        st.write("5. 🧹 Clean up files")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="section-header">🎬 YouTube Video URL</div>', unsafe_allow_html=True)
        video_url = st.text_input("Enter YouTube video URL:", placeholder="https://youtu.be/...")
        
        if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
            if not video_url:
                st.error("❌ Please enter a YouTube video URL")
                return
                
            if not api_key:
                st.error("❌ Please enter your NVIDIA API key")
                return
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Step 1: Extract comments
                status_text.info("🎬 Extracting comments from YouTube...")
                progress_bar.progress(20)
                
                extractor = YouTubeCommentExtractor(video_url)
                comment_count = extractor.extract_comments()
                
                st.success(f"✅ Extracted {comment_count} comments successfully!")
                
                # Step 2: Translate comments
                status_text.info("🌐 Translating comments to English...")
                progress_bar.progress(50)
                
                translator = CommentTranslator()
                translated_count = translator.translate_comments()
                
                st.success(f"✅ Translated {translated_count} comments successfully!")
                
                # Step 3: Analyze sentiment
                status_text.info("🎭 Analyzing sentiment...")
                progress_bar.progress(80)
                
                analyzer = SentimentAnalyzer(api_key)
                results, sentiment_counts = analyzer.analyze_comments()
                
                progress_bar.progress(100)
                status_text.success("🎉 Analysis complete!")
                
                # Display results
                st.markdown('<div class="section-header">📊 Sentiment Analysis Results</div>', unsafe_allow_html=True)
                
                # Create charts
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    # Bar chart
                    fig_bar = px.bar(
                        x=list(sentiment_counts.keys()),
                        y=list(sentiment_counts.values()),
                        title="Sentiment Distribution",
                        color=list(sentiment_counts.keys()),
                        color_discrete_map={
                            'Positive': '#00CC96',
                            'Negative': '#EF553B',
                            'Neutral': '#636EFA'
                        }
                    )
                    fig_bar.update_layout(
                        xaxis_title="Sentiment",
                        yaxis_title="Number of Comments",
                        showlegend=False
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with col_chart2:
                    # Pie chart
                    fig_pie = px.pie(
                        values=list(sentiment_counts.values()),
                        names=list(sentiment_counts.keys()),
                        title="Sentiment Percentage",
                        color=list(sentiment_counts.keys()),
                        color_discrete_map={
                            'Positive': '#00CC96',
                            'Negative': '#EF553B',
                            'Neutral': '#636EFA'
                        }
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                # Summary statistics
                total_comments = sum(sentiment_counts.values())
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                
                with col_stat1:
                    st.metric("Total Comments", total_comments)
                with col_stat2:
                    st.metric("Positive", sentiment_counts['Positive'], f"{sentiment_counts['Positive']/total_comments*100:.1f}%")
                with col_stat3:
                    st.metric("Negative", sentiment_counts['Negative'], f"{sentiment_counts['Negative']/total_comments*100:.1f}%")
                with col_stat4:
                    st.metric("Neutral", sentiment_counts['Neutral'], f"{sentiment_counts['Neutral']/total_comments*100:.1f}%")
                
                # Detailed results
                st.markdown('<div class="section-header">📝 Detailed Comment Analysis</div>', unsafe_allow_html=True)
                
                for result in results:
                    sentiment_color = {
                        'Positive': '🟢',
                        'Negative': '🔴',
                        'Neutral': '🟡'
                    }
                    
                    with st.expander(f"{sentiment_color[result['overall_sentiment']]} Comment {result['statement_number']}: {result['text'][:50]}..."):
                        st.write(f"**Full Text:** {result['text']}")
                        st.write(f"**Sentiment:** {result['overall_sentiment']}")
                        st.write(f"**Confidence:** {result['confidence']}%")
                        st.write(f"**Key Words:** {result['key_words']}")
                        st.write(f"**Reasoning:** {result['reasoning']}")
                
                # Clean up files
                cleanup_files()
                st.info("🧹 Temporary files cleaned up successfully!")
                
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                cleanup_files()
    
    with col2:
        st.markdown('<div class="section-header">ℹ️ Instructions</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
        <h4>How to use:</h4>
        <ol>
        <li>Enter your NVIDIA API key in the sidebar</li>
        <li>Paste a YouTube video URL</li>
        <li>Click "Start Analysis"</li>
        <li>Wait for the process to complete</li>
        <li>View the sentiment analysis results</li>
        </ol>
        
        <h4>Features:</h4>
        <ul>
        <li>🎬 Automatic comment extraction</li>
        <li>🌐 Multi-language translation</li>
        <li>🎭 AI-powered sentiment analysis</li>
        <li>📊 Interactive visualizations</li>
        <li>🧹 Automatic cleanup</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
