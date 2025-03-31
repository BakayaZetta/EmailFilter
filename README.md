# 🔒 Detectish: Phishing Detection using Artificial Intelligence

French version : [here](./README-fr.md)

## 🌟 Introduction

**Detectish** is a containerized solution that sets up an email analysis infrastructure using various technologies. With this solution, you can view the analysis results, see which tests failed, and check the list of quarantined emails. For users with limited cybersecurity knowledge, we have integrated Mistral AI (via an API token) that provides detailed explanations of why certain tests failed and why an email was quarantined.

## 🛠️ Features

Detectish analyzes emails using multiple methods:

- **SPF Analysis** (Sender Policy Framework) [SPF](https://en.wikipedia.org/wiki/Sender_Policy_Framework)
- **DMARC Analysis** (Domain-based Message Authentication) [DMARC](https://en.wikipedia.org/wiki/DMARC)
- **DKIM Analysis** (DomainKeys Identified Mail) [DKIM](https://en.wikipedia.org/wiki/DomainKeys_Identified_Mail)
- **Attachment Analysis** with [ClamAV](https://www.clamav.net/)
- **Link Analysis** using a fine-tuned BERT model
- **Email Text Analysis** using the same BERT model
- **Blacklist** functionality to automatically quarantine specific email addresses

The emails are then stored in a MySQL database. The web interface is developed using **Vue.js** for the frontend and **Express.js** for the backend.

## Screenshot

TODO

## 🚀 Analysis Performance

The artificial intelligence used reaches an accuracy of nearly 95%. The tests were conducted on a dataset available on [Kaggle](https://www.kaggle.com/datasets/subhajournal/phishingemails).

- **Confusion Matrix**  
  ![Confusion Matrix](./img/confusion_matrix.png)

- **Confusion Matrix (Percentage)**  
  ![Percentage Confusion Matrix](./img/matrix_percentage_confusion.png.png)

> Over 10,000 emails were analyzed, as illustrated by the results above.

The AI model is available on [Hugging Face](https://huggingface.co/ealvaradob/bert-finetuned-phishing).

## 🏗️ Setup and Configuration

### Prerequisites

- **Docker** & **Docker Compose**
- A machine with a minimum of **4 GB RAM** (8 GB recommended for better performance)
- A `.env` file containing the following configuration variables:

```env
MISTRAL_API_KEY=mistral_api_key

DB_NAME=detectish_db
DB_USER=detectish_user
DB_PASSWORD=detectish_password
DB_HOST=localhost
DB_PORT=3306

CLAMAV_HOST=localhost
CLAMAV_PORT=3310

# Web configuration
BACKEND_PORT=3000
FRONTEND_PORT=8000

JWT_SECRET=your_secure_random_string_here
```

### Installation Steps

1. **Clone the repository**:

   ```bash
   git clone https://github.com/Matth-L/detectish.git
   cd detectish
   ```

2. **Build and start the Docker containers**:
   ```bash
   docker-compose up -d
   ```

## 👥 Authors

- **Esteban Becker**
- **Matthias Lapu**
- **Eliséo Chaussoy**
