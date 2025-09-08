import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score
import joblib
from config import SPEECH_CSV_FILE, ML_MODEL

data = pd.read_csv(SPEECH_CSV_FILE)

def process_mfccs(df):
    import ast
    df['MFCCs'] = df['MFCCs'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
    df['MFCCs_mean'] = df['MFCCs'].apply(lambda x: np.mean(x) if isinstance(x, list) else np.nan)
    df['MFCCs_std'] = df['MFCCs'].apply(lambda x: np.std(x) if isinstance(x, list) else np.nan)
    df['MFCCs_max'] = df['MFCCs'].apply(lambda x: np.max(x) if isinstance(x, list) else np.nan)
    df['MFCCs_min'] = df['MFCCs'].apply(lambda x: np.min(x) if isinstance(x, list) else np.nan)
    df.drop('MFCCs', axis=1, inplace=True)
    df.fillna(0, inplace=True)
    return df

data = process_mfccs(data)
X = data.drop('Mood', axis=1)
y = data['Mood']

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)

cv_scores = cross_val_score(rf, X_scaled, y, cv=5)
print(f"Cross-Validation Accuracy: {cv_scores.mean()}")

y_pred = rf.predict(X_test)
print("Test Accuracy:", accuracy_score(y_test, y_pred))

joblib.dump(rf, ML_MODEL)
rf = joblib.load(ML_MODEL)
