#!/usr/bin/env python3
"""
generate_with_references.py
----------------------------
1. Takes a meme concept/topic as input
2. Searches the API for visually similar reference images (embed search)
3. Sends those reference images + analysis context to GPT-4o Image Generation
4. Returns the generated meme image

Usage:
  python generate_with_references.py "wizard pig crypto panic"
  python generate_with_references.py  (interactive prompt)
"""

import base64
import json
import os
import sys
import textwrap
from pathlib import Path

import requests
from dotenv import load_dotenv
from openai import OpenAI

ROOT_DIR = Path(__file__).resolve().parents[1]
FILES_DIR = ROOT_DIR / "files"

load_dotenv(ROOT_DIR / ".env")

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE    = "http://localhost:8000"
STYLE_FILE  = FILES_DIR / "style.md"
SKILL_FILE  = ROOT_DIR / "SKILL.md"
OUTPUT_DIR  = FILES_DIR / "generated_memes"
TOP_K       = 3          # number of reference images to retrieve

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)

OUTPUT_DIR.mkdir(exist_ok=True)


# ── Step 1: Search for reference images ──────────────────────────────────────
def search_references(query: str, k: int = TOP_K) -> list[dict]:
    print(f"\n🔍 Searching for {k} reference images for: '{query}'")
    resp = requests.get(f"{API_BASE}/search", params={"q": query, "k": k}, timeout=30)
    resp.raise_for_status()
    results = resp.json()["results"]
    print(f"   Found {len(results)} references:")
    for r in results:
        print(f"   • {r['id']} (score={r['score']})")
    return results


# ── Step 2: Load reference image bytes ───────────────────────────────────────
def load_image_b64(image_path: str) -> str | None:
    path = Path(image_path)
    if not path.is_absolute():
        path = ROOT_DIR / path
    if path.exists():
        return base64.b64encode(path.read_bytes()).decode()
    # Try fetching from API
    filename = Path(image_path).name
    url = f"{API_BASE}/image/{filename}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return base64.b64encode(r.content).decode()
    except Exception as e:
        print(f"   ⚠️  Could not load image {filename}: {e}")
        return None


# ── Step 3: Build the generation prompt ──────────────────────────────────────
def build_prompt(concept: str, references: list[dict]) -> list[dict]:
    style_guide = STYLE_FILE.read_text(encoding="utf-8") if STYLE_FILE.exists() else ""
    skill_guide = SKILL_FILE.read_text(encoding="utf-8") if SKILL_FILE.exists() else ""

    # System context
    system_text = textwrap.dedent(f"""
        You are a meme generation expert specializing in the Boldleonidas art style.
        
        ## Style Guide
        {style_guide}
        
        ## Skill Blueprint
        {skill_guide}
        
        When generating memes:
        - Study the reference images carefully for layout, character positioning, text placement
        - Replicate the exact visual grammar: panel structure, speech bubbles, character proportions
        - Use the same hand-drawn cartoon aesthetic
        - Make the humor land through timing and character expression
        - Keep text minimal, punchy, crypto/finance themed
    """).strip()

    # Reference context
    ref_descriptions = []
    for i, ref in enumerate(references, 1):
        desc = ref.get("description", "")
        layout = ref.get("layout", {})
        char_pos = ref.get("character_position", {})
        text_style = ref.get("text_style", {})
        content = ref.get("content_structure", "")

        ref_descriptions.append(
            f"Reference {i} ({ref['id']}, similarity={ref['score']}):\n"
            f"  Layout: {json.dumps(layout, ensure_ascii=False)}\n"
            f"  Characters: {json.dumps(char_pos, ensure_ascii=False)}\n"
            f"  Text style: {json.dumps(text_style, ensure_ascii=False)}\n"
            f"  Content: {content}\n"
            f"  Description: {desc}"
        )

    user_text = textwrap.dedent(f"""
        ## Meme Concept to Generate
        {concept}
        
        ## Reference Images Analysis
        {chr(10).join(ref_descriptions)}
        
        ## Task
        Generate a DALL-E image prompt (then generate the image) that:
        1. Captures the concept: "{concept}"
        2. Replicates the visual style from the reference images above
        3. Maintains the Boldleonidas aesthetic (hand-drawn, crypto humor)
        4. Uses panel layout and character placement similar to the references
        
        First output the DALL-E prompt you'll use, then generate the image.
    """).strip()

    # Build messages with reference images as vision context
    messages = [
        {"role": "system", "content": system_text},
    ]

    # Add reference images for vision analysis
    vision_content = [{"type": "text", "text": user_text}]
    loaded_count = 0

    for ref in references:
        b64 = load_image_b64(ref.get("image_path", ""))
        if b64:
            vision_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}",
                    "detail": "high",
                },
            })
            loaded_count += 1

    print(f"   📎 Loaded {loaded_count}/{len(references)} reference images")
    messages.append({"role": "user", "content": vision_content})
    return messages


# ── Step 4: Generate DALL-E prompt via GPT-4o ────────────────────────────────
def get_dalle_prompt(concept: str, references: list[dict]) -> str:
    print("\n🧠 Asking GPT-4o to analyze references and create DALL-E prompt …")
    messages = build_prompt(concept, references)

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=1000,
        temperature=0.8,
    )
    dalle_prompt = resp.choices[0].message.content
    print(f"\n📝 GPT-4o response:\n{dalle_prompt[:500]}…" if len(dalle_prompt) > 500 else f"\n📝 GPT-4o response:\n{dalle_prompt}")
    return dalle_prompt


# ── Step 5: Generate image via DALL-E 3 / GPT-image-1 ────────────────────────
def generate_image(dalle_prompt: str, concept: str) -> str:
    print("\n🎨 Generating image with gpt-image-1 …")

    # Extract the actual prompt if GPT-4o wrapped it in explanation text
    # Look for a prompt block or use the whole thing
    prompt_to_use = dalle_prompt

    # Try to extract just the prompt portion if formatted
    if "DALL-E prompt:" in dalle_prompt:
        prompt_to_use = dalle_prompt.split("DALL-E prompt:")[-1].strip().split("\n")[0]
    elif "```" in dalle_prompt:
        import re
        code_blocks = re.findall(r"```(?:\w+)?\n?(.*?)```", dalle_prompt, re.DOTALL)
        if code_blocks:
            prompt_to_use = code_blocks[0].strip()

    # Ensure it doesn't exceed DALL-E limit
    if len(prompt_to_use) > 4000:
        prompt_to_use = prompt_to_use[:4000]

    resp = client.images.generate(
        model="gpt-image-1",
        prompt=prompt_to_use,
        size="1024x1024",
        quality="high",
        n=1,
    )

    # Save the image
    import time
    safe_concept = "".join(c if c.isalnum() else "_" for c in concept)[:40]
    timestamp = int(time.time())
    out_path = OUTPUT_DIR / f"meme_{safe_concept}_{timestamp}.png"

    image_data = resp.data[0]

    if hasattr(image_data, "b64_json") and image_data.b64_json:
        img_bytes = base64.b64decode(image_data.b64_json)
        out_path.write_bytes(img_bytes)
        print(f"\n✅ Image saved to: {out_path}")
    elif hasattr(image_data, "url") and image_data.url:
        img_resp = requests.get(image_data.url, timeout=60)
        out_path.write_bytes(img_resp.content)
        print(f"\n✅ Image saved to: {out_path}")
    else:
        print("⚠️  No image data returned")
        return ""

    return str(out_path)


# ── Main pipeline ─────────────────────────────────────────────────────────────
def generate_meme(concept: str):
    print(f"\n{'='*60}")
    print(f"🎭 MEME GENERATOR — Boldleonidas Style")
    print(f"{'='*60}")
    print(f"Concept: {concept}")

    # 1. Search for references
    references = search_references(concept, k=TOP_K)

    if not references:
        print("❌ No references found! Make sure the API server is running.")
        return

    # 2. Get DALL-E prompt from GPT-4o
    dalle_prompt = get_dalle_prompt(concept, references)

    # 3. Generate the image
    output_path = generate_image(dalle_prompt, concept)

    print(f"\n{'='*60}")
    print(f"✅ DONE! Meme generated.")
    if output_path:
        print(f"   📁 Output: {output_path}")
    print(f"{'='*60}\n")

    return output_path


if __name__ == "__main__":
    if len(sys.argv) > 1:
        concept = " ".join(sys.argv[1:])
    else:
        concept = input("Enter meme concept: ").strip()
        if not concept:
            concept = "wizard pig explaining why bitcoin will moon but pig is panicking"

    generate_meme(concept)
