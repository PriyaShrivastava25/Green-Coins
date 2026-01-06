# Green Coins- Web Application

Green Coins is a Django-based web application designed to promote eco-friendly activities by rewarding users with Green Coins for verified environmental actions.
The project aims to create awareness, encourage sustainable behavior, and build a scalable Anti-Pollution Market system.

This project is developed as an MCA Capstone Project with real-world use cases and scalability in mind.

## Project Overview

Green Coins allows users to:
- Register and log in securely
- Perform eco-friendly activities (Tree Plantation etc.)
- Submit proofs (image + location)
- Earn Green Coins after approval
- View profile, coins, and leaderboard
- Get tree plantation recommendations based on city, weather, and pollution data


##  Tech Stack

**Backend**
- Python 3.10
- Django 
- SQLite (development)

**Frontend**
- HTML
- CSS
- JavaScript (Vanilla)

**APIs Used**
- Geoapify (Geocoding)
- OpenWeatherMap (Weather & Pollution)
- WeatherAPI (Backup weather data)

## Features

###  User Features
- User registration & login
- Email verification using OTP 
- Submit eco-friendly activity proofs
- Automatic Green Coin calculation
- Profile page with earned coins & rank
- Leaderboard (dynamic ranking)
- Tree recommendation system (city-based)

### Admin Features
- Approve / reject user submissions (manual override if auto-validation fails)
- Automatic coin allocation on approval
- Rejection with reason
- Secure admin panel (Django Admin)

### Smart Validation
- EXIF GPS extraction from images
- Manual or live GPS comparison
- Distance calculation (Haversine formula)
- Auto-accept or reject based on location accuracy



##  Project Structure

green_coins_project/
│
├── green_coins_project/
├── mainapp/ 
├── tree_recommend/ 
├── media/ 
├── GreenCoin_venv/ 
├── db.sqlite3 
├── manage.py
├── .env 
├── .gitignore
└── README.md


##  Environment Variables (.env)

The project uses a `.env` file to keep sensitive information secure.

SECRET_KEY=your_django_secret_key
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_email_app_password

GEOAPIFY_API_KEY=your_geoapify_key
OPENWEATHER_API_KEY=your_openweather_key
WEATHERAPI_KEY=your_weatherapi_key

Note:  Do not commit .env file to GitHub.



## Installation & Setup

###  Clone the repository
```bash
git clone https://github.com/PriyaShrivastava25/Green-Coins.git

cd green_coins_project
```

###  Create & activate virtual environment
```bash
python -m venv GreenCoin_venv
GreenCoin_venv\Scripts\activate
```

###  Install dependencies
```bash
pip install -r requirements.txt
```

###  Setup environment variables
Create a `.env` file in `green_coins_project/` and add required keys.

###  Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

###  Start the server
```bash
python manage.py runserver
```

Open browser:
http://127.0.0.1:8000/


Developer
Priya Shrivastava
MCA Student | Web Development
