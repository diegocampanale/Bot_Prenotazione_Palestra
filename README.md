# Bot Prenotazione Palestra

Un bot progettato per gestire la prenotazione delle sessioni in palestra in modo semplice e automatico.

## 🚀 Funzionalità principali

- Prenotazione di sessioni di allenamento.
- Gestione delle disponibilità.
- Cancellazione delle prenotazioni.
- Notifiche automatiche agli utenti.

## 📦 Struttura del Progetto

- `main.py` — File principale che gestisce il comportamento del bot e dello scheduler automatico.
- `config.py` — File locale che contiene variabili sensibili come il token del bot (non incluso nel repository).
- `requirements.txt` — Librerie Python necessarie per far funzionare il progetto.

## 🔐 Configurazione

1. Crea un file `config.py` nella root del progetto basandoti su `config.example.py`.

Esempio di `config.py`:

```python
BOT_TOKEN = "inserisci_il_tuo_token_qui"
url = "iserisci_l'url_del_tuo_servizio_qui"
```

2. Assicurati che `config.py` sia escluso dal repository (`.gitignore` lo esclude già).

## 🛠️ Setup Locale

1. Clona il repository:

```bash
git clone https://github.com/diegocampanale/Bot_Prenotazione_Palestra.git
cd Bot_Prenotazione_Palestra
```

2. Crea un ambiente virtuale (opzionale ma consigliato):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Installa i requisiti:

```bash
pip install -r requirements.txt
```

4. Esegui il bot:

```bash
python bot.py
```

## ⚙️ Requisiti

- Python 3.8+
- Le librerie elencate in `requirements.txt`



Questo progetto è fornito a scopo didattico e di sviluppo personale.fig.py` o dati sensibili su repository pubblici.

## 📬 Contatti

Realizzato da [Diego Campanale](https://github.com/diegocampanale).