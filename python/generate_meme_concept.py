import os
import sys
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
FILES_DIR = ROOT_DIR / "files"

# Tải biến môi trường từ file .env
load_dotenv(ROOT_DIR / ".env")

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")

if not api_key:
    print("Error: Missing OPENAI_API_KEY. Vui lòng thêm vào file .env")
    sys.exit(1)

client = OpenAI(
    api_key=api_key,
    base_url=base_url if base_url else None
)

def read_style_files():
    # Read style.md if it exists, otherwise return empty
    style_content = ""
    skill_content = ""
    try:
        with open(FILES_DIR / "style.md", "r", encoding="utf-8") as f:
            style_content = f.read()
    except Exception:
        pass
    try:
        with open(ROOT_DIR / "SKILL.md", "r", encoding="utf-8") as f:
            skill_content = f.read()
    except Exception:
        pass
    return style_content, skill_content

def generate_meme(trend, character):
    style_content, skill_content = read_style_files()
    
    prompt = f"""
    Bạn là một AI Agent chuyên tạo meme theo phong cách của tài khoản X @boldleonidas.
    
    Dưới đây là tài liệu Hướng dẫn phong cách (Style Guide) và Skill của Boldleonidas:
    ---
    STYLE GUIDE:
    {style_content}
    
    SKILL INSTRUCTIONS:
    {skill_content}
    ---
    
    Nhiệm vụ của bạn là tạo một ý tưởng meme (Meme Blueprint) và câu lệnh tạo ảnh (DALL-E 3 Image Prompt) kết hợp:
    1. Trending Topic / Post: "{trend}"
    2. Nhân vật chính yêu cầu: "{character}"
    
    Hãy trả về kết quả định dạng Markdown chứa các phần sau:
    1. Phân tích ý tưởng (Concept Analysis): Ý tưởng của meme này là gì? Nhân vật phản ứng ra sao với trend?
    2. Meme Blueprint: Bản phác thảo từng panel (sử dụng đúng format mẫu trong SKILL.md, tất cả text trong speech bubble phải IN HOA - ALL CAPS).
    3. DALL-E 3 Image Prompt: Câu lệnh chi tiết bằng Tiếng Anh để đưa vào DALL-E 3 tạo ra bức ảnh/truyện tranh này theo phong cách vẽ tay đặc trưng của boldleonidas.
    """

    print(f"Đang tạo meme cho trend: '{trend}' với nhân vật: '{character}'...")
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a professional comic writer and meme designer."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        temperature=0.7
    )
    
    return response.choices[0].message.content

def main():
    # Default values or read from command line arguments
    trend = "Gas fees on Ethereum spiked to 500 gwei due to an NFT drop"
    character = "Wizard"
    
    if len(sys.argv) > 1:
        trend = sys.argv[1]
    if len(sys.argv) > 2:
        character = sys.argv[2]
        
    result = generate_meme(trend, character)
    
    # Save output to a file
    output_filename = FILES_DIR / "test_meme_output.md"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(result)
        
    print(f"\nMeme concept generated successfully! Saved to {output_filename}")
    print("\n--- Output Preview ---")
    print(result)

if __name__ == "__main__":
    main()
