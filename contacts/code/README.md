# README: Running the Public Toilet Pathogen Transmission Model

## Overview

This project simulates human-surface contact patterns and pathogen transmission risks in public toilets. It uses a combination of observed behavioral data, a Markov chain to generate realistic surface contact sequences, and a gradient-based contamination transfer model. The final result is an estimation of the contamination levels on a user's hands after a toilet visit, under various scenarios (different toilet types and activities).

## Directory Structure

Your Google Drive folder (e.g., `MyDrive/toilet_observations`) should have the following structure:

toilet_observations/
data/
clean_contact_data.csv       # The observed human-surface interaction dataset
code/
gpt_pro_model.py             # The main model implementation
outputs/                        #Where the model outputs are stored
1_start_here.ipynb               # The main Jupyter notebook for running analyses
README.md                        # This instruction file

### What Each File/Folder Does

- **data/clean_contact_data.csv**: Input dataset containing sequences of surfaces touched, activities, and toilet types.
- **code/gpt_pro_model.py**: Python code defining the `EnhancedToiletModelWithValidation` class. This class:
  - Loads data
  - Builds scenario-specific Markov chains
  - Simulates contamination transfer (surface to hand)
  - Offers validation methods for comparing generated sequences against observed data.
- **notebooks/analysis.ipynb**: The main notebook you will open in Google Colab. It:
  - Mounts your Google Drive
  - Runs the model using `gpt_pro_model.py`
  - Generates and visualizes results (such as violin plots of final hand contamination, length distribution comparisons)
  - Performs statistical tests (KS test for sequence length distributions, Chi-square for transition patterns)
  
- **README.md**: This guide.

## Running the Model in Google Colab

### Prerequisites

- You should have a Google account and access to Google Drive.
- The `clean_contact_data.csv` file should be uploaded to `data/`.
- The `gpt_pro_model.py` file should be in `code/`.
- The `1_start_here.ipynb` should be in `notebooks/`.

### Steps to Run

1. **Open Google Drive**:  
   Go to [https://drive.google.com](https://drive.google.com) and navigate to your `toilet_observations` folder.

2. **Open the Notebook in Colab**:  
   Inside the `notebooks` folder, right-click on `1_start_here.ipynb` → "Open with" → "Google Colab."

   The `1_start_here.ipynb` notebook will open in a new Colab tab.

3. **Mount Google Drive**:  
   The first cell in the notebook typically mounts your Google Drive:
   ```python
   from google.colab import drive
   drive.mount('/content/drive')


   %cd /content/drive/MyDrive/toilet_observations