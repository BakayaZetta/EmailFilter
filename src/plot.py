import json
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to load data from a JSON file
def load_data_from_json(file_path: str) -> Dict[str, Any]:
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

# Function to calculate average scores and total counts
def calculate_statistics(data: Dict[str, Any]) -> tuple[float, float, int, int, float, float]:
    '''
    Calculates average scores and total counts for phishing and benign instances.

    Parameters:
        data (Dict[str, Any]): Data loaded from the JSON file.

    Returns:
        tuple: A tuple containing average phishing score, average benign score, total phishing count, total benign count, phishing percentage, and benign percentage.
    '''
    total_phishing_score = 0
    total_phishing_count = 0
    total_benign_score = 0
    total_benign_count = 0

    for entry in data:
        stats = entry["statistics"]
        total_phishing_score += stats["phishing_count"] * stats["phishing_avg_score"]
        total_phishing_count += stats["phishing_count"]
        total_benign_score += stats["benign_count"] * stats["benign_avg_score"]
        total_benign_count += stats["benign_count"]

    avg_phishing_score = total_phishing_score / total_phishing_count if total_phishing_count != 0 else 0
    avg_benign_score = total_benign_score / total_benign_count if total_benign_count != 0 else 0

    total_count = total_phishing_count + total_benign_count
    phishing_percentage = (total_phishing_count / total_count) * 100 if total_count != 0 else 0
    benign_percentage = (total_benign_count / total_count) * 100 if total_count != 0 else 0

    return avg_phishing_score, avg_benign_score, total_phishing_count, total_benign_count, phishing_percentage, benign_percentage

# Function to plot the counts and percentages of phishing and benign instances
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

# Main analysis function
def analyze_data(file_path: str) -> None:
    '''
    Analyzes data from a JSON file and plots the results.

    Parameters:
        file_path (str): Path to the JSON file.

    Returns:
        None
    '''
    data = load_data_from_json(file_path)
    avg_phishing_score, avg_benign_score, total_phishing_count, total_benign_count, phishing_percentage, benign_percentage = calculate_statistics(data)

    logging.info(f"Average Phishing Score: {avg_phishing_score}")
    logging.info(f"Average Benign Score: {avg_benign_score}")
    logging.info(f"Total Phishing Count: {total_phishing_count}")
    logging.info(f"Total Benign Count: {total_benign_count}")
    logging.info(f"Phishing Percentage: {phishing_percentage:.2f}%")
    logging.info(f"Benign Percentage: {benign_percentage:.2f}%")

    plot_counts_and_percentages(total_phishing_count, total_benign_count, phishing_percentage, benign_percentage)

# Run the analysis
file_path = '1.json'  
analyze_data(file_path)
