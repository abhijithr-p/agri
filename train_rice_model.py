import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Input, Lambda
from sklearn.linear_model import LogisticRegression
import glob
from PIL import Image

data_dir = r"c:\Users\USER\agri\rice_leaf_diseases"

print("Building Robust Feature Extractor (MobileNetV2)...")
inputs = Input(shape=(224, 224, 3))
x = tf.keras.layers.Rescaling(1./255)(inputs)
x = Lambda(lambda img: (img * 2.0) - 1.0)(x)
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
base_model.trainable = False
x = base_model(x, training=False)
features_out = GlobalAveragePooling2D()(x)

feature_extractor = Model(inputs, features_out)

print("Extracting features from the dataset...")
X = []
y = []

# Class folders map alphabetically
classes = sorted([d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))])
print(f"Classes: {classes}")

for idx, cls in enumerate(classes):
    cls_dir = os.path.join(data_dir, cls)
    image_paths = glob.glob(os.path.join(cls_dir, "*.*"))
    for img_path in image_paths:
        try:
            img = Image.open(img_path).convert("RGB")
            img = img.resize((224, 224))
            img_array = np.array(img, dtype=np.float32)
            img_array = np.expand_dims(img_array, axis=0)
            
            # Extract 1280-dim feature vector
            feat = feature_extractor.predict(img_array, verbose=0)[0]
            X.append(feat)
            y.append(idx)
        except Exception:
            continue

X = np.array(X)
y = np.array(y)
print(f"Collected {len(X)} images. Training Logistic Regression for optimal deterministic weights...")

# Train deterministic Logistic Regression (immune to mode collapse)
clf = LogisticRegression(max_iter=2000, multi_class='multinomial')
clf.fit(X, y)
print(f"Logistic Regression Training Accuracy: {clf.score(X, y)*100:.2f}%")

# Retrieve optimal weights
W = clf.coef_.T  # Shape: (1280, 3)
b = clf.intercept_ # Shape: (3,)

print("Generating Numpy Vector File for pure mathematical deployment...")

model_path = r"c:\Users\USER\agri\backend\model_weights.npz"
np.savez(model_path, W=W, b=b)
print(f"\n✅ Perfect Transfer Learning Matrix saved securely to {model_path}!")
