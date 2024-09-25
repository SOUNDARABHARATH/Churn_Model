from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, LabelEncoder

app = FastAPI()

# Load the RandomForest model and scaler
random_forest_model = joblib.load('RandomForest_model.joblib')
scaler = joblib.load('scaler.joblib')  # Load the scaler used during training

# Pydantic model for request body
class CustomerData(BaseModel):
    tenure: float
    totalcharges: float
    # Include other necessary features based on your dataset
    # Example: monthlycharges: float

# Data Preprocessing Function
def preprocess_data(df):
    # Impute missing values
    imputer = SimpleImputer(strategy='most_frequent')
    df_imputed = pd.DataFrame(imputer.fit_transform(df), columns=df.columns)

    # Handle categorical variables
    label_encoders = {}
    for column in df_imputed.select_dtypes(include=['object']).columns:
        le = LabelEncoder()
        df_imputed[column] = le.fit_transform(df_imputed[column])
        label_encoders[column] = le
    return df_imputed

# Feature Engineering Function
def feature_engineering(df):
    # Calculate monthly charges if totalcharges and tenure are present
    if 'totalcharges' in df.columns and 'tenure' in df.columns:
        df['monthlycharges'] = df['totalcharges'] / (df['tenure'] + 1)
    return df

@app.post("/predict")
def predict_churn(customer_data: CustomerData):
    # Convert input data to DataFrame
    data = pd.DataFrame([customer_data.dict()])

    # Preprocess the data
    data_preprocessed = preprocess_data(data)
    data_features = feature_engineering(data_preprocessed)

    # Prepare the features for prediction
    X_new = data_features.drop('churn', axis=1, errors='ignore')  # Ignore if 'churn' column is not present

    # Scale the new features
    X_new_scaled = scaler.transform(X_new)

    # Make prediction with the RandomForest model
    prediction = random_forest_model.predict(X_new_scaled)[0]
    
    return {"prediction": prediction}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
