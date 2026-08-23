# Flask App

A basic Flask application boilerplate.

## Structure

```
flask-app/
├── app.py              # Main application & routes
├── config.py           # Configuration
├── requirements.txt    # Python dependencies
├── .env.example         # Example environment variables
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── about.html
│   └── 404.html
└── static/
    ├── css/style.css
    └── js/main.js
```

## Setup

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Run the app
python app.py
```

Visit `http://127.0.0.1:5000` in your browser.

## Notes

- `/api/health` returns a simple JSON health check.
- Update `SECRET_KEY` in `.env` before deploying anywhere real.
