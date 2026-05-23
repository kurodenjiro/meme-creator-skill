---
name: boldleonidas-meme-generator
description: Creates a multi-panel comic meme prompt based on a trending topic and a given character, using the signature Boldleonidas style.
---

# 🎨 Boldleonidas Meme Generator Skill

This skill allows the agent to generate comic-style meme concepts by combining a trending social media post (or topic) and a specific character. It uses the signature "Boldleonidas" comic style synthesized from the analysis of 700+ images.

## 🎯 Objective
Generate a detailed image prompt and dialogue script for a 1-panel, 2-panel, or 3-panel comic meme based on user-provided inputs (a trending topic and a character) conforming to the Boldleonidas style.

## 📝 Inputs
When triggering this skill, the user should provide:
1. **Trending Topic / Post**: The context, joke setup, or market situation.
2. **Character**: The specific character to feature (e.g., Wizard, Frog, Purple PRO Cap, Orange Bitcoin, Pig, cz).

---

## 🎭 Style Profile (Extracted from 700+ Images)

### 1. Layouts
*   **1-Panel (81.0% of memes)**: Best for quick reactions or metaphorical charts. The character occupies 30-40% of one side (typically bottom-left or bottom-right), while the chart/reaction target occupies the rest.
*   **2-Panel (15.7% of memes)**: Setup and Punchline side-by-side or stacked. Character positions must remain identical across panels.
*   **3-Panel (2.3% of memes)**: Sequential dialogues (e.g. Panel 1: knock, Panel 2: look, Panel 3: talk).

### 2. Standard Characters
*   **Wizard/Mage**: Purple robe with yellow stars/moon patterns, pointed wizard hat, long white beard, and expressive white eyebrows.
*   **Green Frog**: PEP-style frog, expressive large eyes, simple expressions.
*   **Purple PRO Hat**: Purple body, black baseball cap with "PRO" in bold white letters.
*   **Orange Bitcoin Coin**: Orange circle coin with BTC symbol, cartoon arms/legs/face.
*   **Pig**: Pink, round pig with wide, expressive eyes.

### 3. Speech Bubbles & Text
*   **Bubbles**: Solid white background, clean black outline. A pointed tail pointing to the speaker's mouth. Located at the top of the panel.
*   **Typography**: **ALL CAPS** black text. Hand-drawn, bold, marker-like comic sans font.

---

## 🚀 Execution Steps

1.  **Analyze the Inputs:**
    *   Identify the core joke, conflict, or irony of the trending topic.
    *   Match the character's archetype to the theme (e.g., Wizard for dev/tech, Green Frog for average trader, Purple PRO Cap for professional).

2.  **Determine Panel Layout:**
    *   If it's a simple reaction or chart metaphor, use a **1-Panel** layout.
    *   If it's a conversation or setup/reaction, use a **2-Panel** layout.

3.  **Draft the Comic Script:**
    *   Write the visual layout, character descriptions, and speech bubble text.
    *   Ensure all bubble text is in **ALL CAPS**.

4.  **Format the Output for Image Generation:**
    Output the final meme blueprint in the following format:

```markdown
### Meme Blueprint

**Layout Type:** [1-Panel / 2-Panel / 3-Panel]
**Primary Character:** [Wizard / Green Frog / Purple PRO Hat / Orange Bitcoin / Pig]

---

**Panel 1:**
*   **Visual Scene:** [Describe the background, e.g., "Flat solid light gray background (#D3D3D3)"]
*   **Character Placement & Size:** [e.g., "Wizard on the left side, occupying 35% of the frame, holding a staff, look of surprise"]
*   **Speech Bubble:** [Top-left, white background, black border] "YOUR ALL-CAPS TEXT HERE"
*   **Secondary Elements:** [e.g., "A rising green candlestick graph on the right side"]

*(If 2-Panel)*
**Panel 2:**
*   **Visual Scene:** [Describe the background, e.g., "Flat solid light gray background (#D3D3D3)"]
*   **Character Placement & Size:** [e.g., "Wizard on the left side, occupying 35% of the frame, smiling and thumbs up"]
*   **Speech Bubble:** [Top-left, white background, black border] "YOUR ALL-CAPS PUNCHLINE"
*   **Secondary Elements:** [e.g., "A tall green candlestick graph towering over the wizard"]
```

5.  **DALL-E 3 Prompt Construction (For rendering):**
    Provide a unified prompt string that can be used directly with an AI Image Generator to render the comic. Example:
    > "A 2-panel comic strip in the style of boldleonidas. Flat light gray backgrounds. Panel 1 (left): A cartoon purple wizard with a long white beard and a star-patterned robe stands on the left, looking worried. A speech bubble above him says 'WHY IS GAS SO HIGH?'. Panel 2 (right): The same purple wizard stands on the left smiling. A speech bubble above him says 'NEVERMIND, THE TX COMPLETED!'. Hand-drawn, black outlines, simple colors."
