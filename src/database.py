import mysql.connector
from mysql.connector import errorcode
import os
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any
from datetime import datetime
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()
class Database:
    def __init__(self):
        self.db_name: str = os.getenv('DB_NAME')
        self.db_user: str = os.getenv('DB_USER')
        self.db_password: str = os.getenv('DB_PASSWORD')
        self.db_host: str = os.getenv('DB_HOST')
        self.db_port: str = os.getenv('DB_PORT')
        self.conn: Optional[mysql.connector.connection.MySQLConnection] = None
        self.cursor: Optional[mysql.connector.cursor.MySQLCursor] = None
        self.connect()
        self.create_tables()
    def connect(self) -> None:
        try:
            self.conn = mysql.connector.connect(
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            self.cursor = self.conn.cursor()
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_name}")
            self.conn.database = self.db_name
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                logging.error("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                logging.error("Database does not exist")
            else:
                logging.error(err)
    def create_tables(self) -> None:
        tables: Dict[str, str] = {
            "Utilisateur": (
                "CREATE TABLE IF NOT EXISTS Utilisateur ("
                "  ID_Utilisateur INT AUTO_INCREMENT PRIMARY KEY,"
                "  Nom VARCHAR(255),"
                "  Prenom VARCHAR(255),"
                "  Email VARCHAR(255),"
                "  Mot_de_passe VARCHAR(255),"
                "  Role VARCHAR(255)"
                ")"
            ),
            "Mail": (
                "CREATE TABLE IF NOT EXISTS Mail ("
                "  ID_Mail INT AUTO_INCREMENT PRIMARY KEY,"
                "  ID_Utilisateur INT,"
                "  Sujet VARCHAR(255),"
                "  Contenu LONGTEXT,"
                "  Date_Reception DATETIME,"
                "  Statut VARCHAR(255),"
                "  FOREIGN KEY (ID_Utilisateur) REFERENCES Utilisateur(ID_Utilisateur)"
                ")"
            ),
            "Role_Regle_Filtrage": (
                "CREATE TABLE IF NOT EXISTS Role_Regle_Filtrage ("
                "  Role VARCHAR(255) PRIMARY KEY,"
                "  Description TEXT,"
                "  Criteres TEXT"
                ")"
            ),
            "Analyse": (
                "CREATE TABLE IF NOT EXISTS Analyse ("
                "  ID_Analyse INT AUTO_INCREMENT PRIMARY KEY,"
                "  ID_Mail INT,"
                "  Resultat_Analyse TEXT,"
                "  Date_Analyse DATETIME,"
                "  Type_Analyse VARCHAR(255),"
                "  FOREIGN KEY (ID_Mail) REFERENCES Mail(ID_Mail)"
                ")"
            ),
            "Piece_Jointe": (
                "CREATE TABLE IF NOT EXISTS Piece_Jointe ("
                "  ID_Piece_Jointe INT AUTO_INCREMENT PRIMARY KEY,"
                "  ID_Mail INT,"
                "  Nom_Fichier VARCHAR(255),"
                "  Type_Fichier VARCHAR(255),"
                "  Taille_Fichier INT,"
                "  Statut_Analyse VARCHAR(255),"
                "  FOREIGN KEY (ID_Mail) REFERENCES Mail(ID_Mail)"
                ")"
            ),
            "Lien": (
                "CREATE TABLE IF NOT EXISTS Lien ("
                "  ID_Lien INT AUTO_INCREMENT PRIMARY KEY,"
                "  ID_Mail INT,"
                "  URL TEXT,"
                "  Statut_Analyse VARCHAR(255),"
                "  FOREIGN KEY (ID_Mail) REFERENCES Mail(ID_Mail)"
                ")"
            )
        }
        for table_name, table_description in tables.items():
            try:
                logging.info(f"Creating table {table_name}: ")
                self.cursor.execute(table_description)
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                    logging.info("already exists.")
                else:
                    logging.error(err.msg)
            else:
                logging.info("OK")
    def add_mail(self, id_utilisateur: int, sujet: str, contenu: str, date_reception: datetime, statut: str) -> int:
        add_mail_query = (
            "INSERT INTO Mail (ID_Utilisateur, Sujet, Contenu, Date_Reception, Statut) "
            "VALUES (%s, %s, %s, %s, %s)")
        mail_data = (id_utilisateur, sujet, contenu, date_reception, statut)
        self.cursor.execute(add_mail_query, mail_data)
        self.conn.commit()
        return self.cursor.lastrowid
    def add_utilisateur(self, nom: str, prenom: str, email: str, mot_de_passe: str, role: str) -> int:
        add_utilisateur_query = (
            "INSERT INTO Utilisateur (Nom, Prenom, Email, Mot_de_passe, Role) "
            "VALUES (%s, %s, %s, %s, %s)")
        utilisateur_data = (nom, prenom, email, mot_de_passe, role)
        self.cursor.execute(add_utilisateur_query, utilisateur_data)
        self.conn.commit()
        return self.cursor.lastrowid
    def add_analyse(self, id_mail: int, resultat_analyse: str, date_analyse: datetime, type_analyse: str) -> int:
        add_analyse_query = (
            "INSERT INTO Analyse (ID_Mail, Resultat_Analyse, Date_Analyse, Type_Analyse) "
            "VALUES (%s, %s, %s, %s)")
        analyse_data = (id_mail, resultat_analyse, date_analyse, type_analyse)
        self.cursor.execute(add_analyse_query, analyse_data)
        self.conn.commit()
        return self.cursor.lastrowid
    def get_mail(self, id_mail: int) -> Optional[Dict[str, Any]]:
        get_mail_query = "SELECT * FROM Mail WHERE ID_Mail = %s"
        self.cursor.execute(get_mail_query, (id_mail,))
        return self.cursor.fetchone()
    def get_utilisateur(self, id_utilisateur: int) -> Optional[Dict[str, Any]]:
        get_utilisateur_query = "SELECT * FROM Utilisateur WHERE ID_Utilisateur = %s"
        self.cursor.execute(get_utilisateur_query, (id_utilisateur,))
        return self.cursor.fetchone()
    def get_analyse(self, id_analyse: int) -> Optional[Dict[str, Any]]:
        get_analyse_query = "SELECT * FROM Analyse WHERE ID_Analyse = %s"
        self.cursor.execute(get_analyse_query, (id_analyse,))
        return self.cursor.fetchone()
    def update_mail_status(self, id_mail: int, new_status: str) -> None:
        update_status_query = "UPDATE Mail SET Statut = %s WHERE ID_Mail = %s"
        self.cursor.execute(update_status_query, (new_status, id_mail))
        self.conn.commit()
    def user_exists(self, id_utilisateur: int) -> bool:
        get_user_query = "SELECT * FROM Utilisateur WHERE ID_Utilisateur = %s"
        self.cursor.execute(get_user_query, (id_utilisateur,))
        return self.cursor.fetchone() is not None
