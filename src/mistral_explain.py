import subprocess
import os
import json
from mistralai import Mistral
from dotenv import load_dotenv

# Charger les variables d'environnement depuis un fichier .env si disponible
# (utile pour le développement local)
load_dotenv()

def send_curl_requests(filename):
    directory = 'phishing_email_example'
    url = 'http://0.0.0.0:6969/analyse'

    file_path = os.path.join(directory, filename)
    result = subprocess.run([
        'curl', '-X', 'POST', url, '-F', f'file=@{file_path}'
    ], capture_output=True, text=True)
    return result.stdout 

def generate_explanation(email_data):
    """
    Génère une explication structurée pour un email en utilisant Mistral
    
    Args:
        email_data (dict): Les données complètes de l'email et son analyse
        
    Returns:
        str: L'explication générée par Mistral
    """
    try:
        model = "mistral-large-latest"

        # Récupérer la clé API depuis les variables d'environnement
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("La clé API Mistral n'est pas configurée dans les variables d'environnement")
            
        client = Mistral(api_key=api_key)
        
        # Extraire et organiser les informations importantes pour l'analyse
        organized_data = {
            "email": {
                "subject": email_data.get("subject") or "Sans objet",
                "sender": email_data.get("sender") or "Inconnu",
                "receiver": email_data.get("user", {}).get("email") or "Inconnu",
                "date": email_data.get("receivedDate") or "Inconnue",
                "status": email_data.get("status") or "Inconnu"
            },
            "analysis": {
                "spf": next((a.get("result") for a in email_data.get("analyses", []) if a.get("type") == "SPF"), "Inconnu"),
                "dkim": next((a.get("result") for a in email_data.get("analyses", []) if a.get("type") == "DKIM"), "Inconnu"),
                "dmarc": next((a.get("result") for a in email_data.get("analyses", []) if a.get("type") == "DMARC"), "Inconnu"),
                "malware_scan": next((a.get("result") for a in email_data.get("analyses", []) if a.get("type") == "CLAMAV"), "Inconnu"),
                "phishing_score": next((a.get("result") for a in email_data.get("analyses", []) if a.get("type") == "AI"), "Inconnu"),
                "urls": [link.get("url") for link in email_data.get("links", [])]
            }#,
            #"detailed_analysis": email_data.get("analysis") or email_data.get("analyse_details") or []
        }
        
        # Convertir les données organisées en JSON pour le prompt
        analysis_json = json.dumps(organized_data, indent=2, ensure_ascii=False)
        
        # Construire un prompt plus riche et structuré
        system_prompt = """
Tu es un expert en sécurité informatique qui explique en français simple pourquoi un email a été filtré. 
Ta mission est d'analyser les données techniques et d'expliquer de manière claire et accessible les raisons pour lesquelles l'email a été considéré comme suspect.

Voici la structure des données que tu vas analyser:
- email: les informations de base sur l'email (expéditeur, destinataire, sujet, date)
- analysis: les résultats des différentes analyses de sécurité (SPF, DKIM, DMARC, analyse antivirus, score de phishing)
- detailed_analysis: analyses détaillées complémentaires

Règles à suivre:
1. Ton explication doit être claire et compréhensible pour des non-experts
2. Identifie les principaux problèmes de sécurité détectés
3. Explique pourquoi ces problèmes sont préoccupants
4. Si les informations sont insuffisantes, indique-le clairement
5. Utilise un format structuré avec des titres et sous-titres
6. Évite le jargon technique sauf si tu l'expliques
        """
        
        # Préparer les messages pour Mistral
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"Voici les données de l'email à analyser: {analysis_json}"},
            {"role": "user", "content": "Pourquoi cet email a-t-il été filtré? Explique-moi les problèmes de sécurité détectés de façon claire et précise."}
        ]
        
        # Appel à l'API Mistral
        chat_response = client.chat.complete(
            model=model,
            messages=messages,
            max_tokens=2000
        )
        
        # Retourner la réponse
        explanation = chat_response.choices[0].message.content
        
        # Si l'explication est trop générique, ajouter un avertissement
        if "je n'ai pas d'informations suffisantes" in explanation.lower() or "informations manquantes" in explanation.lower():
            explanation += "\n\n---\n\n**Note technique**: Les données fournies pour l'analyse étaient insuffisantes ou incomplètes. Assurez-vous que l'ensemble des analyses de sécurité sont correctement configurées et disponibles."
            
        return explanation
    except Exception as e:
        print(f"Une erreur s'est produite lors de l'appel à Mistral: {e}")
        return f"Impossible de générer une explication pour cet email. Erreur: {str(e)}"

def answer(filename):
    try:
        email_data = json.loads(send_curl_requests(filename))
        explanation = generate_explanation(email_data)
        print(explanation)
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")

if __name__ == '__main__':
    filename="test_SPF.eml"
    print(send_curl_requests(filename))
    answer(filename)
