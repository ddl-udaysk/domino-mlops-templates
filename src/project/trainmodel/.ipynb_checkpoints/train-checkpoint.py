import mlflow
import numpy as np
from data import X_train, X_val, y_train, y_val
from sklearn.linear_model import Ridge, ElasticNet
from xgboost import XGBRegressor
from sklearn.model_selection import ParameterGrid
from params import ridge_param_grid, elasticnet_param_grid, xgb_param_grid
from utils import eval_metrics
from datetime import datetime



print('MLFLOW_TRACKING_URI: ' + os.environ['MLFLOW_TRACKING_URI'])
client = mlflow.tracking.MlflowClient()
myprefix=''

now = datetime.now()
date_time_str = now.strftime("%m-%d-%Y")

experiment_name = 'demo'+'-' + os.environ['DOMINO_STARTING_USERNAME'] + '-' + os.environ['DOMINO_PROJECT_NAME']
model_name = 'demo'+'-' + os.environ['DOMINO_PROJECT_NAME']
if myprefix!='':
    experiment_name = myprefix + '-' + experiment_name
print(experiment_name)

experiment = client.get_experiment_by_name(name=experiment_name)
if(experiment is None):
    print('Creating experiment ')
    client.create_experiment(name=experiment_name)
    experiment = client.get_experiment_by_name(name=experiment_name)

print(experiment_name)
mlflow.set_experiment(experiment_name=experiment_name)

# Loop through the hyperparameter combinations and log results in separate runs
for params in ParameterGrid(elasticnet_param_grid):
    with mlflow.start_run():

        lr = ElasticNet(**params)

        lr.fit(X_train, y_train)

        y_pred = lr.predict(X_val)

        metrics = eval_metrics(y_val, y_pred)

        # Logging the inputs such as dataset
        mlflow.log_input(
            mlflow.data.from_numpy(X_train.toarray()),
            context='Training dataset'
        )

        mlflow.log_input(
            mlflow.data.from_numpy(X_val.toarray()),
            context='Validation dataset'
        )

        # Logging hyperparameters
        mlflow.log_params(params)

        # Logging metrics
        mlflow.log_metrics(metrics)

        # Log the trained model
        mlflow.sklearn.log_model(
            lr,
            "ElasticNet",
            registered_model_name=model_name
            input_example=X_train,
            code_paths=['train.py','params.py','utils.py']
        )