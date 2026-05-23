import os
import glob
import json
import base64
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from openai import OpenAI
import openai
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
FILES_DIR = ROOT_DIR / "files"

# Tải biến môi trường từ file .env
load_dotenv(ROOT_DIR / ".env")

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")

if not api_key:
    raise ValueError("Missing OPENAI_API_KEY. Vui lòng thêm vào file .env")

client = OpenAI(
    api_key=api_key,
    base_url=base_url if base_url else None
)

TEMP_DIR = FILES_DIR / "analysis_results_temp"
ANALYSIS_FILE = FILES_DIR / "analysis_results.json"
IMAGE_DIR = FILES_DIR / "gallery-dl/twitter/boldleonidas"
os.makedirs(TEMP_DIR, exist_ok=True)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image(image_path):
    base64_image = encode_image(image_path)
    
    prompt = """
    Bạn là một chuyên gia thiết kế meme và phân tích mạng xã hội.
    Hãy phân tích bức ảnh này (được lấy từ trang X của boldleonidas) và trích xuất các thông tin sau để làm dữ liệu hướng dẫn cho AI Agent tạo meme:
    1. Bố cục (Layout): Các thành phần văn bản, nhân vật, nền được sắp xếp như thế nào?
    2. Vị trí nhân vật: Nhân vật thường nằm ở đâu trong khung hình? Kích thước chiếm bao nhiêu %?
    3. Nội dung hội thoại / Text: Phông chữ (nếu đoán được), kiểu dáng, màu sắc, vị trí đặt chữ.
    4. Cấu trúc nội dung: Meme này truyền tải thông điệp theo format nào? (ví dụ: So sánh, reaction, fact, v.v.)
    Trả về kết quả dưới dạng JSON với các keys: layout, character_position, text_style, content_structure, description.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "low"
                        }
                    }
                ]
            }
        ],
        max_tokens=500
    )
    
    content = response.choices[0].message.content
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    return json.loads(content)

def analyze_image_with_retry(image_path, max_retries=5):
    delay = 2
    for attempt in range(max_retries):
        try:
            return analyze_image(image_path)
        except (openai.RateLimitError, openai.APIError) as e:
            if attempt == max_retries - 1:
                raise e
            sleep_time = delay * (2 ** attempt) + random.uniform(0.1, 1.0)
            print(f"Lỗi RateLimit/API cho {os.path.basename(image_path)}: {e}. Thử lại sau {sleep_time:.2f} giây (lần {attempt + 1}/{max_retries})...")
            time.sleep(sleep_time)
        except Exception as e:
            raise e

def merge_results():
    results = {}
    # 1. Load existing analysis_results.json
    if ANALYSIS_FILE.exists():
        try:
            with open(ANALYSIS_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
        except Exception:
            results = {}
            
    # 2. Load and merge all temp json files
    temp_files = glob.glob(os.path.join(TEMP_DIR, "*.json"))
    for temp_path in temp_files:
        img_name = os.path.basename(temp_path).replace(".json", "")
        try:
            with open(temp_path, "r", encoding="utf-8") as f:
                results[img_name] = json.load(f)
        except Exception as e:
            print(f"Lỗi đọc file tạm {temp_path}: {e}")
            
    # 3. Save back to analysis_results.json
    with open(ANALYSIS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return results

def main():
    image_files = glob.glob(str(IMAGE_DIR / "*.jpg"))
    
    if not image_files:
        print("Không tìm thấy ảnh nào.")
        return
        
    # Merge existing data to sync
    results = merge_results()

    # Lọc ảnh chưa phân tích
    to_analyze = []
    for img_path in image_files:
        img_name = os.path.basename(img_path)
        temp_file_path = os.path.join(TEMP_DIR, f"{img_name}.json")
        
        # Skip if already in results or temp file exists
        if img_name in results or os.path.exists(temp_file_path):
            continue
        to_analyze.append(img_path)
        
    total_to_analyze = len(to_analyze)
    print(f"Tổng số ảnh JPG: {len(image_files)}, Đã phân tích/có sẵn: {len(image_files) - total_to_analyze}, Cần phân tích: {total_to_analyze}")
    
    if not to_analyze:
        print("Tất cả ảnh đã được phân tích.")
        return

    completed_count = 0
    file_lock = threading.Lock()
    
    def process_file(img_path):
        nonlocal completed_count
        img_name = os.path.basename(img_path)
        temp_file_path = os.path.join(TEMP_DIR, f"{img_name}.json")
        try:
            analysis = analyze_image_with_retry(img_path)
            # Write to its own temp file first (thread-safe since files are unique)
            with open(temp_file_path, "w", encoding="utf-8") as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)
                
            with file_lock:
                completed_count += 1
                print(f"[{completed_count}/{total_to_analyze}] Đã phân tích xong: {img_name}")
        except Exception as e:
            print(f"Lỗi vĩnh viễn với {img_name}: {e}")

    # Chạy song song với 10 threads
    max_workers = 10
    print(f"Bắt đầu phân tích song song với {max_workers} workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_file, path): path for path in to_analyze}
        for future in as_completed(futures):
            pass
            
    # Final merge and save
    print("Đang gộp tất cả kết quả...")
    merge_results()
    print("Phân tích hoàn tất! Dữ liệu được lưu trong analysis_results.json")

if __name__ == "__main__":
    main()
