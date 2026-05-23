# SlideTranslate

Translate and summurize any PDF file.
The program uses Groq API, free and open source.

## Before install

#### Create an API account on Groq

Create an account for free and create an API key on section API.
<https://console.groq.com/https://console.groq.com/>

#### Install the following libraries with pip

```
groq
pymupdf
pdfplumber
questionary
python-dotenv
```

# Install

- Clone the repo
- cd SlideTranslate

Then, create and edit a **.env** file and write your Groq API key :

```bash
GROQ_API_KEY=...
```

# Usage

Run the following command :

```bash
python3 src/main.py
```

# Config

You can edit or create new prompts at the top of main.py
