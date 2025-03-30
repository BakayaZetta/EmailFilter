import os
import subprocess
import os
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

def send_curl_requests(filename):
    directory = 'phishing_email_example'
    url = 'http://0.0.0.0:6969/analyse'

    file_path = os.path.join(directory, filename)
    result = subprocess.run([
        'curl', '-X', 'POST', url, '-F', f'file=@{file_path}'
    ], capture_output=True, text=True)
    return result.stdout 


def mistral_answer(filename):
    try:
        model = "mistral-large-latest"

        api_key = os.environ["MISTRAL_API_KEY"]
        client = Mistral(api_key=api_key)

        # Préparation des messages de contexte
        context_messages = [
            {"role": "system", "content": "Tu es une IA qui explique en français pourquoi les mails n'ont pas été reçu par l'utilisateur. Ton objectif est de fournir des explications claires et compréhensibles aux utilisateurs qui ne sont pas familiers avec les concepts informatiques. Les données qui suivent indiquent les résultats de l'analyse du mail."},
            {"role": "system", "content": send_curl_requests(filename)},
            {"role": "system", "content": "Tu devras expliquer l'élément considéré comme dangereux dans le message précédent."},
        ]

        user_question = "Pourquoi n'ai-je pas reçu le mail ?"
        context_messages.append({"role": "user", "content": user_question})

        # Appel à l'API Mistral
        chat_response = client.chat.complete(
            model=model,
            messages=context_messages
)

        # Affichage de la réponse
        print(chat_response.choices[0].message.content)

    except Exception as e:
        print(f"Une erreur s'est produite : {e}")


if __name__ == '__main__':
    filename="test_SPF.eml"
    print(send_curl_requests(filename))
    mistral_answer(filename)
