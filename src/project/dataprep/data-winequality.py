import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
import json
import os

#Read in data
path = "../../../data/WineQualityData.csv"
df = pd.read_csv(path)
print('Read in {} rows of data'.format(df.shape[0]))

#rename columns to remove spaces
for col in df.columns:
    df.rename({col: col.replace(' ', '_')}, axis =1, inplace = True)

#Create is_red variable to store red/white variety as int    
df['is_red'] = df.type.apply(lambda x : int(x=='red'))

#Find all pearson correlations of numerical variables with quality
corr_values = df.corr().sort_values(by = 'quality')['quality'].drop('quality',axis=0)

#Keep all variables with above a 8% pearson correlation
important_feats=corr_values[abs(corr_values)>0.08]

#Get data set up for model training and evaluation

#Drop NA rows
df = df.dropna(how='any',axis=0)
#Split df into inputs and target
X = df[important_feats.keys()]
y = df['quality'].astype('float64')
#Create 70/30 train test split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

X_train_path = str('/mnt/data/local/{}/WineQualityData-{}.csv'.format(os.environ.get('DOMINO_PROJECT_NAME'),"X_train"))
X_test_path = str('/mnt/data/local/{}/WineQualityData-{}.csv'.format(os.environ.get('DOMINO_PROJECT_NAME'),"X_test"))
y_train_path = str('/mnt/data/local/{}/WineQualityData-{}.csv'.format(os.environ.get('DOMINO_PROJECT_NAME'),"y_train"))
y_test_path = str('/mnt/data/local/{}/WineQualityData-{}.csv'.format(os.environ.get('DOMINO_PROJECT_NAME'),"y_test"))

X_train.to_csv(X_train_path, index=False)
X_test.to_csv(X_test_path, index=False)
y_train.to_csv(y_train_path, index=False)
y_test.to_csv(y_test_path, index=False)