import fitz
import pdfplumber
import base64
import os
from groq import Groq
from dotenv import load_dotenv

import questionary
from rich.console import Console
from rich.progress import track

PATH = "./assets/slides.6.pdf"
OUTPUT_DIR = "./assets/images"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

HELLO_WORLD = """Retourne exactement : Hello World !"""
HARD_SYNTHESIS_PROMPT = """Tu es un assistant pédagogique universitaire. 
Tu reçois le contenu de slides de cours (texte extrait + figures).
Tu dois produire une synthèse structurée, fidèle au contenu source, sans rien inventer.

Respecte EXACTEMENT cette structure :

## 1. Objectif du cours
2-3 phrases résumant ce que ce cours cherche à transmettre.

## 2. Concepts clés
Liste de 5 à 8 concepts centraux, chacun avec une définition courte et précise ainsi qu'un exemple tiré du cours ou le cas échéant inventé mais revérifié'
Format : **Concept** : définition
                        ```Exemple```

## 3. Points essentiels à retenir
5 bullet points synthétisant les idées les plus importantes.
Ce sont les points qu'un étudiant doit absolument avoir compris.

## 4. Ce que je dois savoir faire
Compétences pratiques ou théoriques attendues après ce cours.
Format : liste de verbes d'action (savoir calculer, savoir distinguer, être capable de...)


---
Règles :
- Sois concis et précis, pas de remplissage
- Ne reformule pas les slides mot pour mot, synthétise vraiment
- Si une figure apporte une information clé, mentionne-la brièvement
- Réponds en anglais
- utilise ** mot **  pour tous les mots de vocabulaire
"""


PROMPTS = [HELLO_WORLD, HARD_SYNTHESIS_PROMPT]


def extract_text(path: str) -> str:
    with pdfplumber.open(path) as pdf:
        return "\n\n".join(
            page.extract_text() for page in pdf.pages if page.extract_text()
        )


def extract_images(path: str) -> list[str]:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    doc = fitz.open(path)
    images_b64 = []

    for page_num, page in enumerate(doc):
        for img in page.get_images():
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            if pix.n > 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)

            img_path = f"{OUTPUT_DIR}/page{page_num + 1}_img{len(images_b64)}.png"
            pix.save(img_path)

            with open(img_path, "rb") as f:
                images_b64.append(base64.b64encode(f.read()).decode("utf-8"))

    print(f"{len(images_b64)} images extraites.")
    return images_b64


# Request LLM for summurize
def ask_groq(text: str, images_b64: list[str], prompt: str) -> str:
    client = Groq(api_key=GROQ_API_KEY)

    content = [
        {"type": "text", "text": prompt},
        {"type": "text", "text": f"\n\n--- TEXTE DES SLIDES ---\n{text}"},
    ]

    for img_b64 in images_b64[:5]:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_b64}"},
            }
        )

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": content}],
        temperature=0.5,
        max_tokens=2048,
    )

    return response.choices[0].message.content


def askVariables():
    console = Console()

    prompt = questionary.select(
        "Choose a prompt : ", choices=[f"{i + 1}. {p}" for i, p in enumerate(PROMPTS)]
    ).ask()
    ind = int(prompt.split(".")[0]) - 1
    prompt = PROMPTS[ind]

    pdf_path = questionary.text(
        "Place your PDF file in assets/ folder then write the filename :"
    ).ask()
    #    output_path = questionary.text("Define the output folder :", default="./dist").ask()
    pdf_path = "assets/" + pdf_path
    track(summarizePDF(prompt, pdf_path))

    console.print("Work done !")


def summarizePDF(prompt: str, path: str):
    load_dotenv()

    print("Extracting du text...")
    text = extract_text(path)

    print("Extracting images...")
    images = extract_images(path)

    print("Summurizing...")
    result = ask_groq(text, images, prompt)

    print(result)


if __name__ == "__main__":
    askVariables()
