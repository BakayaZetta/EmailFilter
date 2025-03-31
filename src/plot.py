import json
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from typing import Dict, Any
import numpy as np 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data_from_json(file_path) :
    '''
    Loads data from a JSON file.

    Parameters:
        file_path (str): Path to the JSON file.

    Returns:
        Dict[str, Any]: Data loaded from the JSON file.
    '''
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def calculate_statistics(data: Dict[str, Any]):
    """
    Classifies instances as phishing or benign based on a 90% benign threshold.

    Parameters:
        data (Dict[str, Any]): Data loaded from the JSON file.

    Returns:
        tuple: (total_phishing_count, total_benign_count, phishing_percentage, benign_percentage)
    """
    total_phishing_count = 0
    total_benign_count = 0

    for v in data.values():
        phishing_count = v["phishing_count"]
        benign_count = v["benign_count"]
        total_count = phishing_count + benign_count

        if total_count == 0:
            continue  # Skip empty cases

        benign_percentage = (benign_count / total_count) * 100
        if benign_percentage > 50:
            total_benign_count += 1
        else:
            total_phishing_count += 1

    total_instances = total_phishing_count + total_benign_count
    phishing_percentage = (total_phishing_count / total_instances) * 100 if total_instances else 0
    benign_percentage = (total_benign_count / total_instances) * 100 if total_instances else 0

    return total_phishing_count, total_benign_count, phishing_percentage, benign_percentage


def plot_counts_and_percentages(total_phishing_count: int, total_benign_count: int, phishing_percentage: float, benign_percentage: float) -> None:
    '''
    Plots the counts and percentages of phishing and benign instances.

    Parameters:
        total_phishing_count (int): Total count of phishing instances.
        total_benign_count (int): Total count of benign instances.
        phishing_percentage (float): Percentage of phishing instances.
        benign_percentage (float): Percentage of benign instances.

    Returns:
        None
    '''
    labels = ['Phishing', 'Benign']
    counts = [total_phishing_count, total_benign_count]
    percentages = [phishing_percentage, benign_percentage]

    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.bar(labels, counts, color=['red', 'green'], alpha=0.6, label='Counts')
    ax1.set_xlabel('Type')
    ax1.set_ylabel('Count')
    ax1.set_title('Counts and Percentages of Phishing and Benign Instances')

    ax2 = ax1.twinx()
    ax2.plot(labels, percentages, color='blue', marker='o', linestyle='dashed', linewidth=2, label='Percentages')
    ax2.set_ylabel('Percentage (%)')

    fig.tight_layout()
    plt.legend(loc='upper right')
    plt.show()

def analyze_data(file_path: str) -> None:
    '''
    Analyzes data from a JSON file and plots the results.

    Parameters:
        file_path (str): Path to the JSON file.

    Returns:
        None
    '''
    data = load_data_from_json(file_path)
    total_phishing_count, total_benign_count, phishing_percentage, benign_percentage = calculate_statistics(data)

    logging.info(f"Total Phishing Count: {total_phishing_count}")
    logging.info(f"Total Benign Count: {total_benign_count}")
    logging.info(f"Phishing Percentage: {phishing_percentage:.2f}%")
    logging.info(f"Benign Percentage: {benign_percentage:.2f}%")

def get_confusion_matrix(data):
    '''
    Compute a tuple, (confusion_matrix,confusion_matrix_percentage) from the kaggle_result.json
    '''
    true_benign = 0 # vrai négatif
    false_benign = 0 # faux négatif
    true_phishing = 0 # vrai positif
    false_phishing = 0 # faux positif

    for element in data:
        actual = "phishing" if element.get('Email Type') == "Phishing Email" else "benign"
        predicted = [l["label"] for e in element.get('Result', []) for l in e] 

        for res in predicted: 
            if res == "phishing" and actual == "phishing":
                true_phishing += 1
            elif res == "benign" and actual == "benign":
                true_benign += 1
            elif res == "phishing" and actual == "benign":
                false_phishing += 1
            elif res == "benign" and actual == "phishing": 
                false_benign += 1

    confusion_matrix = np.array([[true_phishing, false_phishing], 
                     [false_benign, true_benign]])

    # percentage 

    total_benign = true_benign + false_benign
    total_phishing = false_phishing + true_phishing

    true_negatif_percent= true_benign / total_benign * 100
    false_negatif_percent= 100-true_negatif_percent

    true_positif_percent = true_phishing / total_phishing * 100
    false_positif_percent = 100-true_positif_percent

    matrix_percentage = np.array([
    [true_positif_percent,false_positif_percent],
    [false_negatif_percent,true_negatif_percent] ]
    )
    
    return (confusion_matrix,matrix_percentage)




def plot_confusion_matrix(conf_matrix,filename):
    '''
    Plot a confusion matrix and saves it using the filename given as argument
    '''
    matrix_labels = [
        ["Vrai phishing", ""],
        ["Faux Bénin", "Vrai Bénin"]
    ]

    plt.figure(figsize=(6,5))
    
    sns.heatmap(conf_matrix, annot=True, cmap="Blues", fmt='g', xticklabels=matrix_labels[1], yticklabels=matrix_labels[0])
    
    plt.title("Matrice de Confusion")
    plt.savefig(filename, bbox_inches="tight")
    plt.close()  

if __name__ == "__main__":

    # analysizing data 

    # phishing= 'result_phishing.json'  
    # benign= 'result_safe.json'  
    # analyze_data(phishing)
    # analyze_data(benign)

    # plotting matrix confusion

    data = load_data_from_json("result_kaggle.json")
    confusion_matrix,matrix_percentage = get_confusion_matrix(data)
    plot_confusion_matrix(confusion_matrix,"confusion_matrix.png")
    plot_confusion_matrix(matrix_percentage,"matrix_percentage_confusion.png")

