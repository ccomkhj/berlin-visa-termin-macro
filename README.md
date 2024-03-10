# Macro Berlin Ausländerbehörde Termin Bot

A Selenium-based bot designed to help individuals secure an appointment with the Landesamt für Einwanderung, commonly known as the Ausländerbehörde, in Berlin.

This project was initiated in response to the challenges many face when trying to book appointments through conventional means, and as a counteraction against those exploiting the scarcity of appointments for financial gain. By providing this bot as an open-source solution, we aim to level the playing field and empower all individuals, regardless of their technical expertise.

## How It Works

The bot utilizes Selenium to automate the process of checking for available appointments on the [Landesamt für Einwanderung's booking page](https://otv.verwalt-berlin.de/ams/TerminBuchen). When an appointment becomes available, the bot can notify the user via a Slack message and an audible alert, allowing them to take immediate action.

### Prerequisites

To use this bot, you'll need:
- Python 3.x
- pip
- virtualenv (recommended)

### Setup Instructions

1. Clone the repository to your local machine:
   ```
   git clone https://github.com/capital-G/berlin-auslanderbehorde-termin-bot.git
   ```
2. Create and activate a virtual environment:
   ```
   virtualenv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```
4. Download the appropriate version of `chromedriver` for your system from [here](https://chromedriver.chromium.org/downloads) and place it in the project directory.
5. Adjust configurations in `config.yaml` and `macro_termin.py` to match your personal details and preferences. 

### Running the Bot

Execute the bot by running:
```
python macro_termin.py
```

## Configuration and Customization

The bot's behavior can be configured by modifying the `config.yaml` file. This includes setting personal information, wait times, and the sound file for alerts. For detailed customization, users can modify the source code as per their needs.

## Acknowledgments

The automation script requires `chromedriver` and Selenium. Refer to the official [Selenium documentation](https://www.selenium.dev/documentation/en/) for more information on web automation.

## License

This project is licensed under the AGPL-3.0 license - see the LICENSE file for details.

### Disclaimer

Please use this bot responsibly. The developers are not responsible for any misuse of this software or any violations of terms and conditions of the Landesamt für Einwanderung booking system.