# Custody Project

## Overview
This project was developed to create court data for a research study on the economic impact of custody on families. The repository contains code for processing and extracting text from court rulings, organizing the extracted data into a structured dataset, and utilizing machine learning methods for document classification.

## Repository Structure

- **OCR_scans/**: Contains scripts for extracting text from manually scanned custody rulings using OCR. The extracted text is saved as `.txt` files.
- **custodydata.py**: The main script that processes custody ruling files (both `.txt` files from scans and `.pdf` files from digitized court documents) to extract relevant information and save it as a `.csv` dataset.
- **searchterms.py**: Defines the search terms used for extracting key variables with a simple text search approach.
- **machine_learning/**: Contains machine learning-based methods for:
  - Detecting the page rotation of scanned documents/photos.
  - Classifying pages to identify appendix pages.
- **helper_files/**: Includes miscellaneous helper scripts used during development, such as:
  - Automating file movements.
  - Comparing names to detect spelling mistakes.

## Python Scripts Overview

- **OCR_imgs.py**: Processes images of scanned custody rulings, applying OCR to extract text.
- **OCR_judgepics.py**: Specifically handles OCR for judge-related images and extracts relevant textual data.
- **OCR_pdfs.py**: Extracts text from PDF documents using OCR, designed for digitized court documents.
- **Similarity_Johanna.py**: Contains code for analyzing textual similarity between different custody rulings.
- **appendix_classification.py**: Implements a model to classify pages as appendix or non-appendix pages.
- **clean_judges.py**: Cleans and processes judge-related information extracted from court documents.
- **clean_judges_SOFI.py**: Similar to `clean_judges.py`, but specifically tailored for SOFI data.
- **crop_image.py**: Crops and preprocesses images before OCR or machine learning processing.
- **custodydata.py**: Extracts relevant text from custody ruling files (scanned `.txt` and digitized `.pdf`) and compiles the data into a structured `.csv` file.
- **move_files.py**: Automates the movement of files for better organization.
- **page_dewarp.py**: Uses machine learning techniques to correct distortions in scanned pages.
- **read_pdf_stella.py**: Reads and extracts text from PDF files using Stella’s processing techniques.
- **searchterms.py**: Contains predefined search terms used for extracting specific information from custody rulings.
- **signature_extractor.py**: Detects and extracts signatures from scanned custody ruling documents.
- **testingcode.py**: Contains various test scripts and experimental code for development and debugging purposes.

## Installation & Usage

### Prerequisites
Ensure you have the following installed:
- Python 3.x
- Required dependencies (install with `pip install -r requirements.txt` if applicable)
- Swedish BERT Model bert-base-swedish-cased, installation guide here: https://huggingface.co/KB/bert-base-swedish-cased

### Running the OCR Processing
```bash
python OCR_scans/ocr_pdfs.py
```

### Extracting Court Data
```bash
python custodydata.py
```

### Running Machine Learning Models
```bash
python machine_learning/ml_rotation.py
python machine_learning/ml_appendix_classifier.py
```

## Contributing
Since the sole purpose of this project is the creation of a data set for a research project, please refrain from spontaneous contributions. Any comments about the existing code are appreciated and should be directed to canessa [at] ifo [.] de.

## License
This project is open-source. Please check the repository for licensing details.

## Contact
For questions or collaboration, feel free to reach out via the repository issues section.

---
[GitHub Repository](https://github.com/scanessa/custodyproject/tree/main)
