# AttendEase

Smart Attendance Management System using QR codes and a simple web interface.

## Description

AttendEase lets students sign in / log in, scan a QR code to mark attendance, and stores attendance data in a SQLite database.  
This is a simple Flask-based web application intended for college use.  

## Features  

- User registration & login  
- QR code scanning to mark attendance  
- SQLite database to store user & attendance data  
- Basic HTML + CSS frontend  
- Single-file (or small) Flask backend for easy deployment  

## ✅ Prerequisites

- Python 3.x  
- `Flask` (and any other libraries listed in `requirements.txt`)  
- (Optional but recommended) a virtual environment  

## 🔧 Setup & Run Locally

1. Clone or download this repository  
2. Create and activate a virtual environment (recommended)  
   ```bash
   python -m venv venv
   source venv/bin/activate    # On Windows: venv\Scripts\activate

Install dependencies
    pip install -r requirements.txt

Run the application
    python app.py

Open your browser and go to http://localhost:5000 (or the port shown in terminal)

