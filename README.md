# 🔐 The Trifecta of Security  
## Blockchain-Integrated Cryptographic Steganography for Data Protection

---

## 📌 Project Overview
The digital era has enabled rapid and large-scale content sharing, but it has also introduced serious concerns related to data privacy, ownership, and misuse. This project presents a secure image-sharing platform that integrates **cryptography, steganography, blockchain, and AI-based sentiment analysis** to provide a robust solution for data protection and authenticity verification.

Secret messages are first analyzed using **VADER sentiment analysis** to prevent harmful content, encrypted using **AES-GCM**, embedded into images using **LSB steganography**, and verified through **blockchain-based hash storage** to ensure immutability and trust.

---

## 🎯 Objectives
- Securely embed secret messages inside images using steganography  
- Encrypt sensitive data using **AES-256 (GCM mode)**  
- Prevent misuse by filtering harmful or negative content using **VADER sentiment analysis**  
- Ensure image authenticity and ownership using **blockchain technology**  
- Detect duplicate or tampered images using **perceptual hashing**

---

## 🛠️ Technologies Used
- **Python** – Core backend programming  
- **Flask** – RESTful API framework  
- **Flask-CORS** – Cross-origin request handling  
- **VADER SentimentIntensityAnalyzer** – Sentiment analysis  
- **AES-GCM (Cryptography library)** – Secure encryption  
- **LSB Steganography (Stegano / PIL)** – Data hiding in images  
- **Blockchain (Ethereum + Ganache)** – Immutable hash storage  
- **Web3.py** – Blockchain interaction  
- **Pandas** – Emoji sentiment processing  

---

## 🧠 System Architecture
1. User enters a secret message  
2. Message is analyzed using **VADER sentiment analysis**  
3. If the message is **negative**, embedding is blocked  
4. Approved messages are encrypted using **AES-GCM**  
5. Encrypted data is embedded into an image using **LSB steganography**  
6. Image hashes (SHA-256 and perceptual hash) are stored on the blockchain  
7. Uploaded images are verified for duplication or tampering  

---

## 🔍 Sentiment Analysis Logic
- VADER calculates:
  - Positive score
  - Negative score
  - Neutral score
  - Compound score (–1 to +1)

### Classification:
- **Positive** → compound ≥ 0.05  
- **Neutral** → –0.05 < compound < 0.05  
- **Negative** → compound ≤ –0.05  

Negative messages are blocked to prevent harmful or unsafe content.

---

## 🔒 Security Features
- **AES-GCM encryption** ensures data confidentiality and integrity  
- **LSB steganography** hides encrypted data without noticeable image distortion  
- **Blockchain storage** ensures immutability and ownership verification  
- **Perceptual hashing** detects duplicate or near-duplicate images  

---

## 💻 Installation & Setup

## Clone the repository
git clone https://github.com/chandanashetty31/Trifecta.git

## Navigate to the project directory
cd Trifecta

## Navigate to frontend
cd /frontend/my-app

## start the app
npm start

## Navigate to backend
cd backend

## Install dependencies
pip install -r requirements.txt

## Run the Flask application
python app.py
