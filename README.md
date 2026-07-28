# Catan Randomizer Site

A Flask website based on the original Python Catan randomizer.

## Run locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Features

- 3–4 player and 5–6 player layouts
- Correct resource and number pools
- Prevents adjacent 6 and 8 tokens
- Uses the uploaded custom tile artwork
- Responsive layout for desktop and mobile
