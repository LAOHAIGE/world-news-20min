import os
import requests
import json
from datetime import datetime
from openai import OpenAI

# 1. 设置：从 GitHub Secrets 获取密钥
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
REPO_OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY").split("/")[-1]

client = OpenAI(api_key=OPENAI_API_KEY)

def get_news():
    print("正在抓取新闻...")
    # 抓取美国头条新闻 (您可以把 country=us 改为 country=cn，如果源支持的话)
    url = f"https://newsapi.org/v2/top-headlines?country=us&category=general&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        articles = data.get('articles', [])[:10] # 取前10条
        
        summary = ""
        for i, art in enumerate(articles):
            title = art.get('title', 'No Title')
            desc = art.get('description', '') or ''
            summary += f"{i+1}. {title}: {desc}\n"
        return summary
    except Exception as e:
        print(f"Error fetching news: {e}")
        return ""

def generate_script(news_summary):
    print("正在编写播客稿件...")
    prompt = f"""
    You are a professional news anchor for a podcast called 'World News 20min'.
    Based on the following news summaries, write a professional news broadcast script in Traditional Chinese (Mandarin).
    
    Requirements:
    - Tone: Professional, neutral, broadcast style (like CCTV or BBC).
    - Structure: 
      1. Intro ("欢迎收听20分钟世界新闻...");
      2. Detailed news reporting;
      3. Outro ("感谢收听，明天见。").
    - Content: Summarize the key points clearly.
    - Length: Approximately 1500 Chinese characters.
    - Format: Plain text only. No markdown formatting.
    
    News Data:
    {news_summary}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o", # 如果觉得贵，可以改成 gpt-3.5-turbo
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def text_to_speech(script):
    print("正在转录语音 (MP3)...")
    # 为了演示简单，我们只截取前4096个字符防止报错，实际使用通常够了
    safe_script = script[:4096]
    
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx", # 男声，比较深沉，适合新闻
        input=safe_script
    )
    # 覆盖保存为同一个文件名，这样APP不用每天变URL
    response.stream_to_file("daily_news.mp3")

def create_manifest():
    print("正在生成播放列表 JSON...")
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 构造下载链接
    raw_url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/daily_news.mp3"
    
    data = {
        "date": today,
        "title": f"全球新闻简报 ({today})",
        "audio_url": raw_url,
        "duration": "20:00" 
    }
    
    with open("latest_episode.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

if __name__ == "__main__":
    news = get_news()
    if news:
        script = generate_script(news)
        text_to_speech(script)
        create_manifest()
        print("任务完成！")
    else:
        print("未获取到新闻数据。")
