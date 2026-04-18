import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle
import os

IMG_SIZE = 64
NUM_SAMPLES = 1000

print("Generating synthetic MRI data...")
X, y = [], []
for i in range(NUM_SAMPLES):
    label = i % 2
    img = np.random.normal(0.3, 0.1, (IMG_SIZE * IMG_SIZE,))
    if label == 1:
        cx = np.random.randint(20, IMG_SIZE-20)
        cy = np.random.randint(20, IMG_SIZE-20)
        for px in range(IMG_SIZE):
            for py in range(IMG_SIZE):
                if (px-cx)**2 + (py-cy)**2 <= 100:
                    idx = px * IMG_SIZE + py
                    if idx < len(img):
                        img[idx] += 0.5
    img = np.clip(img, 0, 1)
    X.append(img)
    y.append(label)

X = np.array(X)
y = np.array(y)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Training model...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

acc = model.score(X_test, y_test)
print(f"Test Accuracy: {acc:.4f}")

save_path = os.path.join(os.path.dirname(__file__), 'brain_tumor_model.pkl')
with open(save_path, 'wb') as f:
    pickle.dump(model, f)
print(f"Model saved: {save_path}")
