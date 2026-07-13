# Examples — Detecting Data Anomalies

## Example 1: Network Intrusion Detection with Isolation Forest

Detect port-scan and DDoS patterns in network flow records.

### Data Preparation

```python
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
import matplotlib.pyplot as plt

# Load network flow data
df = pd.read_csv("network_flows.csv")
print(f"Records: {len(df)}, Columns: {list(df.columns)}")
# Records: 50000, Columns: ['timestamp', 'src_ip', 'dst_ip', 'protocol', 'packet_count', 'byte_volume', 'duration_sec', 'flag']

# Profile feature distributions
print(df[['packet_count', 'byte_volume', 'duration_sec']].describe())
#        packet_count  byte_volume  duration_sec
# count     50000.00     50000.00      50000.00
# mean        142.30    185420.00         12.40
# std         890.50   1250000.00         45.20
# min           1.00        64.00          0.01
# max       98000.00  85000000.00       3600.00

# Encode categorical protocol column
le = LabelEncoder()
df['protocol_encoded'] = le.fit_transform(df['protocol'])

# Select numeric features for anomaly detection
features = ['packet_count', 'byte_volume', 'duration_sec', 'protocol_encoded']
X = df[features].copy()

# Handle missing values
X = X.fillna(X.median())

# Scale features to normalize magnitude differences
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
print(f"Scaled feature shape: {X_scaled.shape}")
# Scaled feature shape: (50000, 4)
```

### Model Training and Detection

```python
# Configure Isolation Forest
# contamination=0.02 means we expect ~2% anomalies
model = IsolationForest(
    n_estimators=200,
    contamination=0.02,
    max_samples='auto',
    max_features=1.0,
    random_state=42,
    n_jobs=-1,
)

# Fit and predict
model.fit(X_scaled)
df['anomaly_score'] = model.decision_function(X_scaled)  # Higher = more normal
df['anomaly_label'] = model.predict(X_scaled)             # -1 = anomaly, 1 = normal

# Summary statistics
anomaly_count = (df['anomaly_label'] == -1).sum()
total = len(df)
print(f"Anomalies detected: {anomaly_count}/{total} ({anomaly_count/total*100:.1f}%)")
# Anomalies detected: 1000/50000 (2.0%)

# Inspect top anomalies by score (most anomalous first)
top_anomalies = df[df['anomaly_label'] == -1].nsmallest(10, 'anomaly_score')
print(top_anomalies[['src_ip', 'dst_ip', 'protocol', 'packet_count', 'byte_volume', 'anomaly_score']])
#          src_ip       dst_ip protocol  packet_count  byte_volume  anomaly_score
# 12045  10.0.0.5  192.168.1.*      TCP         98000     85000000         -0.412
# 8821   10.0.0.9  10.0.0.255       UDP         45000       320000         -0.389
# 33102  10.0.0.3   172.16.0.1      TCP         67000     42000000         -0.375
```

### Visualization

```python
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# 1. Anomaly score distribution
axes[0].hist(df['anomaly_score'], bins=100, color='steelblue', edgecolor='none')
axes[0].axvline(x=df[df['anomaly_label'] == -1]['anomaly_score'].max(),
                color='red', linestyle='--', label='Threshold')
axes[0].set_title('Anomaly Score Distribution')
axes[0].set_xlabel('Decision Function Score')
axes[0].legend()

# 2. Scatter: packet count vs byte volume
normal = df[df['anomaly_label'] == 1]
anomalous = df[df['anomaly_label'] == -1]
axes[1].scatter(normal['packet_count'], normal['byte_volume'],
                s=1, alpha=0.3, label='Normal')
axes[1].scatter(anomalous['packet_count'], anomalous['byte_volume'],
                s=10, c='red', alpha=0.7, label='Anomaly')
axes[1].set_title('Packet Count vs Byte Volume')
axes[1].set_xlabel('Packet Count')
axes[1].set_ylabel('Byte Volume')
axes[1].legend()

# 3. Anomalies over time
df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
hourly_anomalies = df[df['anomaly_label'] == -1].groupby('hour').size()
axes[2].bar(hourly_anomalies.index, hourly_anomalies.values, color='crimson')
axes[2].set_title('Anomalies by Hour of Day')
axes[2].set_xlabel('Hour')
axes[2].set_ylabel('Anomaly Count')

plt.tight_layout()
plt.savefig('network_anomalies.png', dpi=150)
plt.show()
```

### Export Flagged Records

```python
# Export anomalies with contributing features
export_df = df[df['anomaly_label'] == -1][
    ['timestamp', 'src_ip', 'dst_ip', 'protocol', 'packet_count',
     'byte_volume', 'duration_sec', 'anomaly_score']
].sort_values('anomaly_score')

export_df.to_csv('flagged_anomalies.csv', index=False)
print(f"Exported {len(export_df)} flagged records to flagged_anomalies.csv")
# Exported 1000 flagged records to flagged_anomalies.csv
```

---

## Example 2: Manufacturing Quality Control with Local Outlier Factor

Detect equipment degradation from sensor readings.

```python
import pandas as pd
import numpy as np
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import RobustScaler

# Load sensor data: temperature, vibration, pressure per production cycle
df = pd.read_csv("production_cycles.csv")
print(f"Cycles: {len(df)}")
# Cycles: 10000

features = ['temperature_c', 'vibration_mm_s', 'pressure_bar']
X = df[features].copy()

# Use RobustScaler to handle occasional sensor spikes
scaler = RobustScaler()
X_scaled = scaler.fit_transform(X)

# Local Outlier Factor - good for density-varying data
lof = LocalOutlierFactor(
    n_neighbors=20,
    contamination=0.03,
    metric='euclidean',
    n_jobs=-1,
)

# LOF only has fit_predict (no separate predict step)
df['anomaly_label'] = lof.fit_predict(X_scaled)
df['lof_score'] = lof.negative_outlier_factor_  # More negative = more anomalous

anomaly_count = (df['anomaly_label'] == -1).sum()
print(f"Anomalous cycles: {anomaly_count} ({anomaly_count/len(df)*100:.1f}%)")
# Anomalous cycles: 300 (3.0%)

# Time-series visualization with normal operating bands
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

fig, ax = plt.subplots(figsize=(14, 5))
df['cycle_date'] = pd.to_datetime(df['cycle_timestamp'])

normal = df[df['anomaly_label'] == 1]
anomalous = df[df['anomaly_label'] == -1]

ax.plot(normal['cycle_date'], normal['temperature_c'],
        '.', markersize=1, alpha=0.3, color='steelblue', label='Normal')
ax.plot(anomalous['cycle_date'], anomalous['temperature_c'],
        'o', markersize=5, color='red', alpha=0.8, label='Anomaly')

# Normal operating band (mean +/- 2 std)
mean_temp = normal['temperature_c'].mean()
std_temp = normal['temperature_c'].std()
ax.axhspan(mean_temp - 2*std_temp, mean_temp + 2*std_temp,
           alpha=0.1, color='green', label='Normal Band (2 sigma)')

ax.set_title('Equipment Temperature with Anomaly Detection')
ax.set_ylabel('Temperature (C)')
ax.legend()
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
plt.tight_layout()
plt.savefig('manufacturing_anomalies.png', dpi=150)
```

### Expected Output

```
Anomalous cycles: 300 (3.0%)

Top anomalous cycles (by LOF score):
  cycle_id  temperature_c  vibration_mm_s  pressure_bar  lof_score
     4821         312.5            8.90          2.10     -4.82
     7233         298.0           12.30          1.85     -3.91
     1502         285.0            0.12          4.50     -3.67
```

---

## Example 3: Financial Transaction Monitoring with Autoencoder

Flag fraudulent transactions using reconstruction error.

```python
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# Load transaction data (assume labeled for evaluation)
df = pd.read_csv("transactions.csv")
print(f"Transactions: {len(df)}, Fraud rate: {df['is_fraud'].mean():.3f}")
# Transactions: 100000, Fraud rate: 0.012

features = ['amount', 'merchant_category_code', 'hour_of_day',
            'day_of_week', 'distance_from_home_km', 'transaction_count_24h']
X = df[features].values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split: train on legitimate transactions only
legit_mask = df['is_fraud'] == 0
X_train = X_scaled[legit_mask]
X_test = X_scaled  # Evaluate on all data

print(f"Training on {len(X_train)} legitimate transactions")
# Training on 98800 legitimate transactions
```

### Autoencoder Model

```python
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

class TransactionAutoencoder(nn.Module):
    def __init__(self, input_dim: int):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
        )
        self.decoder = nn.Sequential(
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim),
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

# Training
model = TransactionAutoencoder(input_dim=len(features))
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
criterion = nn.MSELoss()

train_tensor = torch.FloatTensor(X_train)
train_loader = DataLoader(TensorDataset(train_tensor, train_tensor),
                          batch_size=256, shuffle=True)

model.train()
for epoch in range(50):
    total_loss = 0
    for batch_x, _ in train_loader:
        optimizer.zero_grad()
        reconstructed = model(batch_x)
        loss = criterion(reconstructed, batch_x)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    if (epoch + 1) % 10 == 0:
        print(f"Epoch {epoch+1}/50, Loss: {total_loss/len(train_loader):.6f}")

# Epoch 10/50, Loss: 0.042318
# Epoch 20/50, Loss: 0.018472
# Epoch 30/50, Loss: 0.009831
# Epoch 40/50, Loss: 0.006214
# Epoch 50/50, Loss: 0.004892
```

### Anomaly Scoring

```python
# Compute reconstruction error on all transactions
model.eval()
with torch.no_grad():
    test_tensor = torch.FloatTensor(X_test)
    reconstructed = model(test_tensor)
    reconstruction_error = torch.mean((test_tensor - reconstructed) ** 2, dim=1).numpy()

df['reconstruction_error'] = reconstruction_error

# Use 99th percentile of training error as threshold
train_errors = reconstruction_error[legit_mask]
threshold = np.percentile(train_errors, 99)
df['predicted_fraud'] = (df['reconstruction_error'] > threshold).astype(int)

# Evaluation
from sklearn.metrics import precision_score, recall_score, f1_score

precision = precision_score(df['is_fraud'], df['predicted_fraud'])
recall = recall_score(df['is_fraud'], df['predicted_fraud'])
f1 = f1_score(df['is_fraud'], df['predicted_fraud'])

print(f"Threshold: {threshold:.4f}")
print(f"Precision: {precision:.3f}, Recall: {recall:.3f}, F1: {f1:.3f}")
print(f"Flagged transactions: {df['predicted_fraud'].sum()}")
# Threshold: 0.0523
# Precision: 0.847, Recall: 0.762, F1: 0.802
# Flagged transactions: 1080

# Show top flagged transactions
flagged = df[df['predicted_fraud'] == 1].nlargest(5, 'reconstruction_error')
print(flagged[['amount', 'merchant_category_code', 'hour_of_day',
               'reconstruction_error', 'is_fraud']])
#      amount  merchant_category_code  hour_of_day  reconstruction_error  is_fraud
# 0   4521.00                    5411         3.00                0.3421         1
# 1   8900.50                    5912         2.00                0.2987         1
# 2    125.00                    7995        23.00                0.2654         1
# 3   3200.00                    5411         4.00                0.2103         1
# 4    999.99                    5999         1.00                0.1876         0
```

---

## Example 4: Quick Anomaly Detection with Simple Statistical Methods

When you have fewer than 500 data points, use Z-score or IQR instead of ML models.

```python
import pandas as pd
import numpy as np

df = pd.read_csv("small_dataset.csv")  # 200 records

# Z-score method
from scipy import stats
df['z_score'] = np.abs(stats.zscore(df['metric_value']))
df['z_anomaly'] = df['z_score'] > 3  # Flag values beyond 3 standard deviations

# IQR method
Q1 = df['metric_value'].quantile(0.25)
Q3 = df['metric_value'].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
df['iqr_anomaly'] = (df['metric_value'] < lower_bound) | (df['metric_value'] > upper_bound)

print(f"Z-score anomalies: {df['z_anomaly'].sum()}")
print(f"IQR anomalies: {df['iqr_anomaly'].sum()}")
print(f"Bounds: [{lower_bound:.2f}, {upper_bound:.2f}]")
# Z-score anomalies: 4
# IQR anomalies: 7
# Bounds: [12.50, 87.30]
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
