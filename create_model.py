import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()

import numpy as np
try:
    import tf_keras as keras
except ImportError:
    import keras

from keras.applications import MobileNetV2
from keras.layers import Dense, GlobalAveragePooling2D, Dropout
from keras.models import Model

print("Building professional Plant Disease ML Model...")
# Base model on ImageNet
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))

# We freeze the base model for transfer learning
for layer in base_model.layers:
    layer.trainable = False

x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dense(256, activation='relu')(x)
x = Dropout(0.5)(x)
predictions = Dense(4, activation='softmax')(x)

model = Model(inputs=base_model.input, outputs=predictions)
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# Create dummy valid data to instantiate the shapes
print("Instantiating shapes with dummy run...")
dummy_input = np.random.rand(1, 224, 224, 3)
model.predict(dummy_input)

model_path = os.path.join(os.path.dirname(__file__), "model.h5")
# Save as .h5 file
model.save(model_path)
print(f"Model saved successfully at: {model_path}")
