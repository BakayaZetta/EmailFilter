import ollama

desiredModel = "deepseek-r1:1.5b"
conversation = []  # Liste pour stocker l'historique des messages

# Ajouter les informations sur SPF, DKIM, DMARC, le phishing, le spoofing et les menaces pour une entreprise à la conversation
conversation.append({
    'role': 'user',
    'content': (
        "Peux-tu m'expliquer ce que sont SPF, DKIM, DMARC, le phishing, le spoofing et les menaces pour une entreprise ? "
        "SPF (Sender Policy Framework) est un protocole qui permet aux propriétaires de domaines de spécifier "
        "quels serveurs de messagerie sont autorisés à envoyer des emails en leur nom. Cela aide à prévenir le spoofing "
        "en vérifiant que les emails proviennent de sources autorisées. "
        "DKIM (DomainKeys Identified Mail) utilise une signature cryptographique pour vérifier que le contenu d'un email "
        "n'a pas été altéré pendant le transit. Cela garantit l'intégrité du message et aide à prouver qu'il provient bien "
        "du domaine déclaré. "
        "DMARC (Domain-based Message Authentication, Reporting & Conformance) s'appuie sur SPF et DKIM pour fournir une "
        "couche supplémentaire de protection. Il permet aux propriétaires de domaines de publier des politiques qui indiquent "
        "comment traiter les emails qui échouent aux vérifications SPF ou DKIM. "
        "Le phishing est une technique de fraude utilisée par des cybercriminels pour obtenir des informations sensibles "
        "telles que des mots de passe, des numéros de carte de crédit, etc. Les attaquants se font passer pour des entités "
        "de confiance et incitent les victimes à divulguer leurs informations personnelles. "
        "Le spoofing est une technique où un attaquant falsifie l'adresse d'expéditeur d'un email pour qu'il semble provenir "
        "d'une source légitime. Cela peut être utilisé pour diffuser des logiciels malveillants ou pour des attaques de phishing. "
        "Les menaces pour une entreprise incluent la perte de données sensibles, les violations de la vie privée, les pertes "
        "financières, et les atteintes à la réputation. Les attaques de phishing et de spoofing peuvent entraîner des fuites "
        "d'informations confidentielles, des interruptions de service, et des coûts élevés pour la remédiation et la récupération."
    )
})

while True:
    questionToAsk = input("question to ask (or 'exit' to quit): ")

    if questionToAsk.lower() == "exit":
        break

    conversation.append({'role': 'user', 'content': questionToAsk})

    response = ollama.chat(model=desiredModel, messages=conversation)

    OllamaResponse = response['message']['content']
    conversation.append({'role': 'assistant', 'content': OllamaResponse})

    print(OllamaResponse)
