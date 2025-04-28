# Gym Booking Bot

A bot designed to manage gym session bookings easily and automatically.

## 🚀 Main Features

- Booking of workout sessions.
- Management of session availability.
- Cancellation of bookings.
- Automatic user notifications.

## 📦 Project Structure

- `main.py` — Main file that manages the bot behavior and the automatic scheduler.
- `config.py` — Local file containing sensitive variables such as the bot token (not included in the repository).
- `requirements.txt` — Python libraries required to run the project.

## 🔐 Configuration

1. Create a `config.py` file in the project root based on `config.example.py`.

Example of `config.py`:

```python
BOT_TOKEN = "insert_your_token_here"
url = "insert_your_service_url_here"
```

2. Make sure that `config.py` is excluded from the repository (`.gitignore` already handles it).

## 🛠️ Local Setup

1. Clone the repository:

```bash
git clone https://github.com/diegocampanale/Bot_Prenotazione_Palestra.git
cd Bot_Prenotazione_Palestra
```

2. Create a virtual environment (optional but recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install the required libraries:

```bash
pip install -r requirements.txt
```

4. Run the bot:

```bash
python main.py
```

## ⚙️ Requirements

- Python 3.8+
- Libraries listed in `requirements.txt`

## 📄 Notes

- This project is provided for educational and personal development purposes only.
- Always protect your bot token and any sensitive data.

## 📬 Contact

Developed by [Diego Campanale](https://github.com/diegocampanale).