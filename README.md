# Genetic Prediction System

A Flask-based web application for genetic predictions using machine learning models. The system can predict gender and ancestry based on genetic data, and uses Google's Gemini AI to generate predictions about physical characteristics and disease risks.

## Setup

### Environment Variables

This application uses environment variables for configuration. Create a `.env` file in the root directory with the following variables:

```
# Flask Secret Key - Used for session encryption
FLASK_SECRET_KEY=your_secure_flask_secret_key_here

# Google Gemini API Key
# Get your API key from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Application Settings
DEBUG=True
PORT=5001
```

### Installing Dependencies

1. Install required Python packages:

```bash
pip install -r requirements.txt
```

### Running the Application

1. Make sure you've set up the `.env` file with your Google Gemini API key
2. Start the application:

```bash
python app.py
```

3. Open your browser and navigate to: http://localhost:5001

## Features

- Gender and ancestry prediction based on genetic data
- Physical characteristics prediction using Google Gemini AI
- Genetic disease risk assessment
- Support for sample data analysis and visualization

## Important Notes

- The AI-based predictions (physical characteristics and disease risks) require a valid Google Gemini API key
- The predictions are based on statistical correlations and should not be used for medical diagnosis
- Sample data must be properly formatted (see documentation) 