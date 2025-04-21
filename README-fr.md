# 🔒 Detectish : Détection de phishing avec intelligence artificielle

Version anglaise : [ici](README.md)

## 📖 Table des matières

- [🌟 Introduction](#-introduction)
- [🛠️ Fonctionnalités](#️-fonctionnalités)
- [📸 Capture d'écran](#capture-décran)
- [🚀 Performances de l'analyse](#-performances-de-lanalyse)
- [🏗️ Installation et Configuration](#️-installation-et-configuration)
  - [Prérequis](#prérequis)
  - [Étapes d'installation](#étapes-dinstallation)
- [Detectish : à quoi ça ressemble ?](#detectish--à-quoi-ça-ressemble-)
- [👥 Auteurs](#-auteurs)
- [⚠️ Avertissement](#avertissement-️)

## 🌟 Introduction

**Detectish** est une solution conteneurisée qui met en place une infrastructure d'analyse des emails à l'aide de diverses technologies. Grâce à cette solution, vous pouvez visualiser les résultats de l'analyse, voir quels tests ont échoué et consulter la liste des emails mis en quarantaine. Pour les utilisateurs ayant peu de connaissances en sécurité informatique, nous avons intégré Mistral AI (via un token API) qui explique de manière détaillée pourquoi certains tests ont échoué et pourquoi l'email a été mis en quarantaine.

## 🛠️ Fonctionnalités

Detectish analyse les emails en utilisant différentes méthodes :

- **Analyse SPF** [(Sender Policy Framework)](https://fr.wikipedia.org/wiki/Sender_Policy_Framework)
- **Analyse DMARC** [(Domain-based Message Authentication)](https://fr.wikipedia.org/wiki/DMARC)
- **Analyse DKIM** [(DomainKeys Identified Mail)](https://fr.wikipedia.org/wiki/DomainKeys_Identified_Mail)
- **Analyse des pièces jointes** avec [ClamAV](https://www.clamav.net/)
- **Analyse des liens** via un modèle BERT fine-tuné
- **Analyse du texte** de l’email avec le même modèle BERT
- **Liste noire** permettant de mettre automatiquement certaines adresses email en quarantaine

Les emails sont ensuite stockés dans une base de données MySQL.
Le site web est développé en **Vue.js** pour le frontend et **Express.js** pour le backend.

## Capture d'écran

TODO

## 🚀 Performances de l'analyse

L'intelligence artificielle utilisée atteint une précision proche de 95 %. Les tests ont été réalisés sur une base de données disponible sur [Kaggle](https://www.kaggle.com/datasets/subhajournal/phishingemails).

<div align="center">

- **Matrice de confusion**  
  ![Matrice de confusion](./img/confusion_matrix.png)

- **Matrice de confusion (pourcentage)**  
  ![Matrice de confusion pourcentage](./img/matrix_percentage_confusion.png)

</div>

> Plus de 10 000 emails ont été analysés avec les résultats présentés ci-dessus.

Le modèle AI est disponible sur [Hugging Face](https://huggingface.co/ealvaradob/bert-finetuned-phishing).

## 🏗️ Installation et Configuration

### Prérequis

- **Docker** & **Docker Compose**
- Une machine avec au minimum **4 Go de RAM disponible pour docker** (8 Go recommandés pour de meilleures performances)
- Un fichier `.env` avec les variables de configuration suivantes :

```env
# Database configuration
DB_NAME=detectish_db
DB_USER=detectish_user
DB_PASSWORD=detectish_password
DB_HOST=mysql
DB_PORT=3306

# MySQL root credentials
MYSQL_ROOT_PASSWORD=MYSQL_ROOT_PASSWORD
MYSQL_DATABASE=detectish_db
MYSQL_USER=detectish_user
MYSQL_PASSWORD=detectish_password

# ClamAV configuration
CLAMAV_HOST=clamav
CLAMAV_PORT=3310

# API Keys
MISTRAL_API_KEY=your_mistral_api_key # Replace with your Mistral API key

# Security
JWT_SECRET=your_secure_random_string_here # Replace with a secure random string

# Frontend configuration
VITE_API_URL=/api
VITE_BACKEND_URL=http://backend:3000
VITE_DETECTISH_URL=http://detectish:6969
```

### Étapes d'installation

1. **Cloner le dépôt** :

   ```bash
   git clone https://github.com/Matth-L/detectish.git
   cd detectish
   ```

2. **Construire et démarrer les conteneurs Docker** :
   ```bash
   docker-compose up -d
   ```

## Detectish : à quoi ça ressemble ?

Voilà à quoi ressemble l'interface de Detectish sans connexion :
![Detectish - Landing page](./img/Landing_page.png)

Avec connexion :
![Detectish - Landing page connecté](./img/Landing_page_connected.png)

La page de quarantaine où vous pouvez voir les emails jugés comme suspicieux ou dangeureux par notre solution:
![Detectish - Page de quarantaine](./img/Quarantine.png)

Explication des résultats d'analyse fournie par Mistral AI :
![Detectish - Page d'explication](./img/Mistral_explanation.png)

Des stats sur les emails analysés afin d'avoir une vue d'ensemble de la situation :
![Detectish - Page de stats](./img/Statisics.png)

La liste noire des emails qui sont mis en quarantaine automatiquement :
![Detectish - Page de liste noire](./img/Blacklist.png)

## 👥 Auteurs

- **Esteban Becker**
- **Matthias Lapu**
- **Eliséo Chaussoy**

### Avertissement ⚠️

Ce projet a été développé dans le cadre d'un travail universitaire. Il n'a jamais été testé en environnement réel, et son bon fonctionnement n'est pas garanti. Utilisez-le à vos risques et périls ! 🚧
