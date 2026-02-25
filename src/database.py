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

    @staticmethod
    def _is_disconnect_error(err: Exception) -> bool:
        disconnect_error_codes = {2006, 2013, 2055, 4031}
        errno = getattr(err, 'errno', None)
        message = str(err).lower()
        return (
            errno in disconnect_error_codes
            or 'lost connection' in message
            or 'disconnected by the server because of inactivity' in message
        )

    def _ensure_connection(self) -> None:
        if self.conn is None:
            self.connect()
            return

        try:
            self.conn.ping(reconnect=True, attempts=1, delay=0)
        except mysql.connector.Error:
            self.connect()

        if self.cursor is None and self.conn is not None:
            self.cursor = self.conn.cursor()

    def _execute(self, query: str, params: tuple = (), retry: bool = True) -> None:
        self._ensure_connection()
        try:
            self.cursor.execute(query, params)
        except mysql.connector.Error as err:
            if retry and self._is_disconnect_error(err):
                logging.warning(f"Database connection dropped, retrying query once: {err}")
                self.connect()
                self.cursor.execute(query, params)
            else:
                raise

    def _commit(self) -> None:
        self._ensure_connection()
        self.conn.commit()

    def connect(self) -> None:
        '''
        Connects to the database and creates the database if it does not exist.

        Parameters:
            None

        Returns:
            None
        '''
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
        '''
        Creates the necessary tables in the database.

        Parameters:
            None

        Returns:
            None
        '''
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
                "  Emetteur VARCHAR(255),"
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
        tables["Blacklist"] = (
            "CREATE TABLE IF NOT EXISTS Blacklist ("
            "  ID_Blacklist INT AUTO_INCREMENT PRIMARY KEY,"
            "  Email VARCHAR(255),"
            "  IP VARCHAR(255),"
            "  Domain VARCHAR(255),"
            "  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
            "  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
            ")"
        )
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
    def add_mail(self, id_utilisateur: int, sujet: str, contenu: str, emetteur:str,date_reception: datetime, statut: str) -> int:
        '''
        Adds a mail record to the database.

        Parameters:
            id_utilisateur (int): The ID of the user.
            sujet (str): The subject of the email.
            contenu (str): The content of the email.
            date_reception (datetime): The date the email was received.
            statut (str): The status of the email.

        Returns:
            int: The ID of the inserted mail record.
        '''
        add_mail_query = (
            "INSERT INTO Mail (ID_Utilisateur, Sujet, Contenu, Date_Reception, Emetteur, Statut) "
            "VALUES (%s, %s, %s, %s, %s, %s)")
        mail_data = (id_utilisateur, sujet, contenu, date_reception, emetteur, statut)
        self._execute(add_mail_query, mail_data)
        self._commit()
        return self.cursor.lastrowid
    def add_utilisateur(self, nom: str, prenom: str, email: str, mot_de_passe: str, role: str) -> int:
        '''
        Adds a user record to the database.

        Parameters:
            nom (str): The last name of the user.
            prenom (str): The first name of the user.
            email (str): The email address of the user.
            mot_de_passe (str): The password of the user.
            role (str): The role of the user.

        Returns:
            int: The ID of the inserted user record.
        '''
        add_utilisateur_query = (
            "INSERT INTO Utilisateur (Nom, Prenom, Email, Mot_de_passe, Role) "
            "VALUES (%s, %s, %s, %s, %s)")
        utilisateur_data = (nom, prenom, email, mot_de_passe, role)
        self._execute(add_utilisateur_query, utilisateur_data)
        self._commit()
        return self.cursor.lastrowid
    def add_analyse(self, id_mail: int, resultat_analyse: str, date_analyse: datetime, type_analyse: str) -> int:
        '''
        Adds an analysis record to the database.

        Parameters:
            id_mail (int): The ID of the email.
            resultat_analyse (str): The result of the analysis.
            date_analyse (datetime): The date of the analysis.
            type_analyse (str): The type of analysis.

        Returns:
            int: The ID of the inserted analysis record.
        '''
        add_analyse_query = (
            "INSERT INTO Analyse (ID_Mail, Resultat_Analyse, Date_Analyse, Type_Analyse) "
            "VALUES (%s, %s, %s, %s)")
        analyse_data = (id_mail, resultat_analyse, date_analyse, type_analyse)
        self._execute(add_analyse_query, analyse_data)
        self._commit()
        return self.cursor.lastrowid
    def get_mail(self, id_mail: int) -> Optional[Dict[str, Any]]:
        '''
        Retrieves a mail record from the database.

        Parameters:
            id_mail (int): The ID of the email.

        Returns:
            Optional[Dict[str, Any]]: The mail record, or None if not found.
        '''
        get_mail_query = "SELECT * FROM Mail WHERE ID_Mail = %s"
        self._execute(get_mail_query, (id_mail,))
        return self.cursor.fetchone()
    def get_utilisateur(self, id_utilisateur: int) -> Optional[Dict[str, Any]]:
        '''
        Retrieves a user record from the database.

        Parameters:
            id_utilisateur (int): The ID of the user.

        Returns:
            Optional[Dict[str, Any]]: The user record, or None if not found.
        '''
        get_utilisateur_query = "SELECT * FROM Utilisateur WHERE ID_Utilisateur = %s"
        self._execute(get_utilisateur_query, (id_utilisateur,))
        return self.cursor.fetchone()
    def get_analyse(self, id_analyse: int) -> Optional[Dict[str, Any]]:
        '''
        Retrieves an analysis record from the database.

        Parameters:
            id_analyse (int): The ID of the analysis.

        Returns:
            Optional[Dict[str, Any]]: The analysis record, or None if not found.
        '''
        get_analyse_query = "SELECT * FROM Analyse WHERE ID_Analyse = %s"
        self._execute(get_analyse_query, (id_analyse,))
        return self.cursor.fetchone()
    def update_mail_status(self, id_mail: int, new_status: str) -> None:
        '''
        Updates the status of a mail record in the database.

        Parameters:
            id_mail (int): The ID of the email.
            new_status (str): The new status of the email.

        Returns:
            None
        '''
        update_status_query = "UPDATE Mail SET Statut = %s WHERE ID_Mail = %s"
        self._execute(update_status_query, (new_status, id_mail))
        self._commit()
    def user_exists(self, id_utilisateur: int) -> bool:
        '''
        Checks if a user exists in the database.

        Parameters:
            id_utilisateur (int): The ID of the user.

        Returns:
            bool: True if the user exists, False otherwise.
        '''
        get_user_query = "SELECT * FROM Utilisateur WHERE ID_Utilisateur = %s"
        self._execute(get_user_query, (id_utilisateur,))
        return self.cursor.fetchone() is not None
    def user_exists_by_email(self, email: str) -> bool:
        '''
        Checks if a user exists in the database by email.

        Parameters:
            email (str): The email address of the user.

        Returns:
            bool: True if the user exists, False otherwise.
        '''
        get_user_query = "SELECT * FROM Utilisateur WHERE Email = %s"
        self._execute(get_user_query, (email,))
        return self.cursor.fetchone() is not None

    def add_user_with_email(self, email: str) -> int:
        '''
        Adds a user record to the database with minimal information.

        Parameters:
            email (str): The email address of the user.

        Returns:
            int: The ID of the inserted user record.
        '''
        add_user_query = (
            "INSERT INTO Utilisateur (Nom, Prenom, Email, Mot_de_passe, Role) "
            "VALUES (%s, %s, %s, %s, %s)")
        user_data = ('', '', email, '', 'user')
        self._execute(add_user_query, user_data)
        self._commit()
        return self.cursor.lastrowid

    def get_user_id_by_email(self, email: str) -> Optional[int]:
        '''
        Retrieves the user ID from the database by email.

        Parameters:
            email (str): The email address of the user.

        Returns:
            Optional[int]: The user ID if found, None otherwise.
        '''
        get_user_id_query = "SELECT ID_Utilisateur FROM Utilisateur WHERE Email = %s"
        self._execute(get_user_id_query, (email,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def add_piece_jointe(self, id_mail: int, nom_fichier: str, type_fichier: str, taille_fichier: int, statut_analyse: str) -> int:
        '''
        Adds an attachment analysis record to the database.

        Parameters:
            id_mail (int): The ID of the email.
            nom_fichier (str): The name of the attachment file.
            type_fichier (str): The type of the attachment file.
            taille_fichier (int): The size of the attachment file.
            statut_analyse (str): The analysis status of the attachment.

        Returns:
            int: The ID of the inserted attachment record.
        '''
        add_piece_jointe_query = (
            "INSERT INTO Piece_Jointe (ID_Mail, Nom_Fichier, Type_Fichier, Taille_Fichier, Statut_Analyse) "
            "VALUES (%s, %s, %s, %s, %s)")
        piece_jointe_data = (id_mail, nom_fichier, type_fichier, taille_fichier, statut_analyse)
        self._execute(add_piece_jointe_query, piece_jointe_data)
        self._commit()
        return self.cursor.lastrowid

    def add_lien(self, id_mail: int, url: str, statut_analyse: str) -> int:
        '''
        Adds a URL analysis record to the database.

        Parameters:
            id_mail (int): The ID of the email.
            url (str): The URL that was analyzed.
            statut_analyse (str): The analysis status of the URL.

        Returns:
            int: The ID of the inserted URL record.
        '''
        add_lien_query = (
            "INSERT INTO Lien (ID_Mail, URL, Statut_Analyse) "
            "VALUES (%s, %s, %s)")
        lien_data = (id_mail, url, statut_analyse)
        self._execute(add_lien_query, lien_data)
        self._commit()
        return self.cursor.lastrowid

    def is_blacklisted(self, email: str, ip: str, domain: str) -> bool:
        '''
        Checks if an email, IP, or domain is in the blacklist.

        Parameters:
            email (str): The sender's email address.
            ip (str): The sender's IP address.
            domain (str): The sender's domain.

        Returns:
            bool: True if any of the parameters are blacklisted, False otherwise.
        '''
        params = []
        conditions = []
        
        if email and email.strip():
            email = email.lower()
            conditions.append("LOWER(Email) = %s")
            params.append(email)
        
        if domain and domain.strip():
            domain = domain.lower()
            conditions.append("LOWER(Domain) = %s")
            params.append(domain)
        
        if ip and ip.strip():
            conditions.append("IP = %s")
            params.append(ip)
        
        if not conditions:
            return False
        
        query = f"SELECT * FROM Blacklist WHERE {' OR '.join(conditions)}"
        
        try:
            self._execute(query, tuple(params))
            result = self.cursor.fetchone() is not None
            logging.info(f"Blacklist check: {query} with params {params} -> Result: {result}")
            return result
        except Exception as e:
            logging.error(f"Error in blacklist check: {e}")
            return False
