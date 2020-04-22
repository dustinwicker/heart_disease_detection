import pandas as pd
import os
from sklearn import preprocessing
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from math import sqrt
from scipy import stats
import datetime as dt
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import PCA
from sklearn.model_selection import cross_val_score, cross_val_predict, train_test_split, GridSearchCV, ShuffleSplit
from sklearn.metrics import confusion_matrix
from sklearn.neighbors import KNeighborsClassifier
from sklearn.feature_selection import RFE
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.exceptions import ConvergenceWarning
import statsmodels.api as sm
import itertools
# import seaborn as sns
# import matplotlib.pyplot as plt

# Increase maximum width in characters of columns - will put all columns in same line in console readout
pd.set_option('expand_frame_repr', False)
# Be able to read entire value in each column (no longer truncating values)
pd.set_option('display.max_colwidth', -1)
# Increase number of rows printed out in console
pd.set_option('display.max_rows', 200)

# Change current working directory to main directory
def main_directory():
    os.chdir(os.path.expanduser('~') + '/PycharmProjects/heart_disease')
main_directory()

# Open Hungarian data set
with open('hungarian.data', 'r') as myfile:
    file = []
    for line in myfile:
        line = line.replace(" ", ", ")
        # Add comma to end of each line
        line = line.replace(os.linesep, ',' + os.linesep)
        line = line.split(', ')
        file.extend(line)

file = [value.replace(",\n", "") for value in file]
# Remove empty strings from list
file = list(filter(None, file))

# Convert list to lists of list
attributes_per_patient = 76
i = 0
new_file = []
while i < len(file):
    new_file.append(file[i:i+attributes_per_patient])
    i += attributes_per_patient

# List of column names
headers = ['id', 'ccf', 'age', 'sex', 'painloc', 'painexer', 'relrest', 'pncaden', 'cp', 'trestbps', 'htn', 'chol',
           'smoke', 'cigs', 'years', 'fbs', 'dm', 'famhist', 'restecg', 'ekgmo', 'ekgday', 'ekgyr', 'dig', 'prop',
           'nitr', 'pro', 'diuretic', 'proto', 'thaldur', 'thaltime', 'met', 'thalach', 'thalrest', 'tpeakbps',
           'tpeakbpd', 'dummy', 'trestbpd', 'exang', 'xhypo', 'oldpeak', 'slope', 'rldv5', 'rldv5e', 'ca', 'restckm',
           'exerckm', 'restef', 'restwm', 'exeref', 'exerwm', 'thal', 'thalsev', 'thalpul', 'earlobe', 'cmo',
           'cday', 'cyr', 'num', 'lmt', 'ladprox', 'laddist', 'diag', 'cxmain', 'ramus', 'om1', 'om2', 'rcaprox',
           'rcadist', 'lvx1', 'lvx2', 'lvx3', 'lvx4', 'lvf', 'cathef', 'junk', 'name']

# Convert lists of list into DataFrame and supply column names
hungarian = pd.DataFrame(new_file, columns=headers)

# List of columns to drop
cols_to_drop =['ccf', 'pncaden', 'smoke', 'cigs', 'years', 'dm', 'famhist', 'dig', 'ca', 'restckm', 'exerckm',
               'restef', 'restwm', 'exeref', 'exerwm', 'thal', 'thalsev', 'thalpul', 'earlobe', 'lmt',
               'ladprox', 'laddist', 'diag', 'cxmain', 'ramus', 'om1', 'om2', 'rcaprox', 'rcadist', 'lvx1',
               'cathef', 'junk', 'name', 'thaltime', 'xhypo', 'slope', 'dummy', 'lvx1', 'lvx2']

# Drop columns from above list
hungarian = hungarian.drop(columns=cols_to_drop)

# Convert all columns to numeric
hungarian = hungarian.apply(pd.to_numeric)

# Method to scale continuous and binary variables (z-score standardization)
scaler = preprocessing.StandardScaler()

## Fix possible patient id issues
# Find ids that are not unique to patients
print(hungarian.id.value_counts()[hungarian.id.value_counts()!=1])
# Fix id 1132 (two different patients are both assigned to this id) - give second patient next id number (id max + 1)
hungarian.loc[139,'id'] = hungarian.id.max() + 1

# Determine number of missing values for each patient (-9 is the missing attribute value)
# Drop patients with "significant" number of missing values in record (use 10%, can adjust accordingly)
### Also do analysis with keeping all patients regardless of number of missing values ###
# Determine missing value percentage per patient
missing_value_perc_per_patient = (hungarian == -9).sum(axis=1)[(hungarian == -9).sum(axis=1) > 0]\
                                     .sort_values(ascending=False)/len([x for x in hungarian.columns if x != 'id'])

# Remove patients with > 10% missing values
hungarian = hungarian.drop(missing_value_perc_per_patient[missing_value_perc_per_patient>0.10].index.values)

# Imputing missing values (marked as -9 per data dictionary)
cols_with_missing_values = [(col, hungarian[col].value_counts()[-9]) for col in list(hungarian) if -9 in hungarian[col].unique()]
# Sort tuples by number of missing values
cols_with_missing_values.sort(key=lambda x: x[1])

### Use KNN to impute missing values ###

variables_not_to_use_for_imputation = ['ekgday', 'cmo', 'cyr', 'ekgyr', 'cday', 'ekgmo', 'num']

# Impute htn
impute_variable = 'htn'

# Obtain list of variables to use for imputation
x_variables = [x for x in list(hungarian) if x not in [x[0] for x in cols_with_missing_values] +
                        variables_not_to_use_for_imputation + ['id']]

# Select x and y variables to use
fix_htn = hungarian[x_variables + [impute_variable]]

# Create list of categorical variables to one-hot encode
categorical_x_variables = ['sex', 'painloc', 'painexer', 'relrest', 'cp', 'nitr', 'pro', 'diuretic', 'exang',
                           'lvx3', 'lvx4', 'lvf']

# One-hot encode categorical variables
for value in categorical_x_variables:
    one_hot = pd.get_dummies(fix_htn[value], prefix=value)
    fix_htn = fix_htn.join(one_hot)
    fix_htn = fix_htn.drop(columns=value)

# Create list of x variables
x_variables = [x for x in list(fix_htn) if x != impute_variable]

# Create DataFrame with missing value(s) to predict on
predict = fix_htn.loc[fix_htn[impute_variable]==-9]
# Set x and y predict DataFrames
predict_x, predict_y = predict[x_variables], predict[impute_variable]

# Create DataFrame to train on
train = fix_htn.loc[~(fix_htn[impute_variable]==-9)]
# Set x and y train DataFrames
train_x, train_y = train[x_variables], train[impute_variable]

# Fit and transform scaler on train_x
train_x = scaler.fit_transform(train_x)

# Transform predict_x
predict_x = scaler.transform(predict_x)

# Obtain k (number of neighbors) by using sqrt(n)
k = round(sqrt(len(train_x)))
print(f"k is {k}.")

# Check to make sure k is odd number
if divmod(k, 2)[1] == 1:
    print("k is an odd number. Good to proceed.")
else:
    print("Need to make k an odd number.")

# Predict value for predict_y
htn_prediction = KNeighborsClassifier(n_neighbors=k, metric='minkowski', weights='distance').fit(train_x, train_y).predict(predict_x)
print(f'The prediction for htn is {htn_prediction[0]}.')

# Supply prediction back to appropriate patient
hungarian.loc[hungarian[impute_variable]==-9, 'htn'] = htn_prediction

# Imputing missing values (marked as -9 per data dictionary)
cols_with_missing_values = [(col, hungarian[col].value_counts()[-9]) for col in list(hungarian) if -9 in hungarian[col].unique()]
# Sort tuples by number of missing values
cols_with_missing_values.sort(key=lambda x:x[1])

# Impute restecg
impute_variable = 'restecg'

# Obtain list of variables to use for imputation
x_variables = [x for x in list(hungarian) if x not in [x[0] for x in cols_with_missing_values] +
                        variables_not_to_use_for_imputation + ['id']]

# Select x and y variables to use - added in 'htn'
fix_restecg = hungarian[x_variables + [impute_variable]]

# Create list of categorical variables to one-hot encode
categorical_x_variables = ['sex', 'painloc', 'painexer', 'relrest', 'cp', 'htn', 'nitr', 'pro', 'diuretic', 'exang',
                           'lvx3', 'lvx4', 'lvf']

# One-hot encode categorical variables
for value in categorical_x_variables:
    one_hot = pd.get_dummies(fix_restecg[value], prefix=value)
    fix_restecg = fix_restecg.join(one_hot)
    fix_restecg = fix_restecg.drop(columns=value)

# Create list of x variables
x_variables = [x for x in list(fix_restecg) if x != impute_variable]

# Create DataFrame with missing value(s) - will predict on
predict = fix_restecg.loc[fix_restecg[impute_variable]==-9]
# Set x and y predict DataFrames
predict_x, predict_y = predict[x_variables], predict[impute_variable]

# Create DataFrame to train on
train = fix_restecg.loc[~(fix_restecg[impute_variable]==-9)]
# Set x and y train DataFrames
train_x, train_y = train[x_variables], train[impute_variable]

# Fit and transform scaler on train_x
train_x = scaler.fit_transform(train_x)

# Transform predict_x
predict_x = scaler.transform(predict_x)

# Obtain k (number of neighbors) by using sqrt(n)
k = round(sqrt(len(train_x)))
print(f"k is {k}.")

# Check to make sure k is odd number
if divmod(k, 2)[1] == 1:
    print("k is an odd number. Good to proceed.")
else:
    print("Need to make k an odd number.")

# Predict value for predict_y
restecg_prediction = KNeighborsClassifier(n_neighbors=k, metric='minkowski', weights='distance').fit(train_x, train_y).predict(predict_x)
print(f'The prediction for restecg is {restecg_prediction[0]}.')

# Supply prediction back to appropriate patient
hungarian.loc[hungarian[impute_variable]==-9, 'restecg'] = restecg_prediction

# Imputing missing values (marked as -9 per data dictionary)
cols_with_missing_values = [(col, hungarian[col].value_counts()[-9]) for col in list(hungarian) if -9 in hungarian[col].unique()]
# Sort tuples by number of missing values
cols_with_missing_values.sort(key=lambda x:x[1])

# Impute prop
# Set y variable
impute_variable = 'prop'

# Obtain list of variables to use for imputation
x_variables = [x for x in list(hungarian) if x not in [x[0] for x in cols_with_missing_values] +
                        variables_not_to_use_for_imputation + ['id']]

# Select x and y variables to use - add in 'htn'
fix_prop = hungarian[x_variables + [impute_variable]]

# Create list of categorical variables to one-hot encode
categorical_x_variables = ['sex', 'painloc', 'painexer', 'relrest', 'cp', 'htn', 'restecg', 'nitr', 'pro', 'diuretic', 'exang',
                           'lvx3', 'lvx4', 'lvf']

# One-hot encode categorical variables
for value in categorical_x_variables:
    one_hot = pd.get_dummies(fix_prop[value], prefix=value)
    fix_prop = fix_prop.join(one_hot)
    fix_prop = fix_prop.drop(columns=value)

# Create list of x variables
x_variables = [x for x in list(fix_prop) if x != impute_variable]

# Create DataFrame with missing value(s) - will predict on
predict = fix_prop.loc[fix_prop[impute_variable]==-9]
# Set x and y predict DataFrames
predict_x, predict_y = predict[x_variables], predict[impute_variable]

# Create DataFrame to train on
train = fix_prop.loc[~(fix_prop[impute_variable]==-9)]
# Set x and y train DataFrames
train_x, train_y = train[x_variables], train[impute_variable]

# Fit and transform scaler on train_x
train_x = scaler.fit_transform(train_x)

# Transform predict_x
predict_x = scaler.transform(predict_x)

# Obtain k (number of neighbors) by using sqrt(n)
k = round(sqrt(len(train_x)))
print(f"k is {k}.")

# Check to make sure k is odd number
if divmod(k, 2)[1] == 1:
    print("k is an odd number. Good to proceed.")
else:
    print("Need to make k an odd number.")

# Predict value for predict_y
prop_prediction = KNeighborsClassifier(n_neighbors=k, metric='minkowski', weights='distance').fit(train_x, train_y).predict(predict_x)
print(f'The prediction for prop is {prop_prediction[0]}.')

# Supply prediction back to appropriate patient
hungarian.loc[hungarian[impute_variable]==-9, 'prop'] = prop_prediction

# Imputing missing values (marked as -9 per data dictionary)
cols_with_missing_values = [(col, hungarian[col].value_counts()[-9]) for col in list(hungarian) if -9 in hungarian[col].unique()]
# Sort tuples by number of missing values
cols_with_missing_values.sort(key=lambda x:x[1])

# Impute thaldur
# Set y variable
impute_variable = 'thaldur'

# Obtain list of variables to use for imputation
x_variables = [x for x in list(hungarian) if x not in [x[0] for x in cols_with_missing_values] +
                        variables_not_to_use_for_imputation + ['id']]

# Select x and y variables to use - add in 'prop'
fix_thaldur = hungarian[x_variables + [impute_variable]]

# Create list of categorical variables to one-hot encode
categorical_x_variables = ['sex', 'painloc', 'painexer', 'relrest', 'cp', 'htn', 'restecg', 'prop', 'nitr', 'pro',
                           'diuretic', 'exang', 'lvx3', 'lvx4', 'lvf']

# One-hot encode categorical variables
for value in categorical_x_variables:
    one_hot = pd.get_dummies(fix_thaldur[value], prefix=value)
    fix_thaldur = fix_thaldur.join(one_hot)
    fix_thaldur = fix_thaldur.drop(columns=value)

# Create list of x variables
x_variables = [x for x in list(fix_thaldur) if x != impute_variable]

# Create DataFrame with missing value(s) - will predict on
predict = fix_thaldur.loc[fix_thaldur[impute_variable]==-9]
# Set x and y predict DataFrames
predict_x, predict_y = predict[x_variables], predict[impute_variable]

# Create DataFrame to train on
train = fix_thaldur.loc[~(fix_thaldur[impute_variable]==-9)]
# Set x and y train DataFrames
train_x, train_y = train[x_variables], train[impute_variable]

# Fit scaler on train_x
train_x = scaler.fit_transform(train_x)

# Transform predict_x
predict_x = scaler.transform(predict_x)

# Obtain k (number of neighbors) by using sqrt(n)
k = round(sqrt(len(train_x)))
print(f"k is {k}.")

# Check to make sure k is odd number
if divmod(k, 2)[1] == 1:
    print("k is an odd number. Good to proceed.")
else:
    print("Need to make k an odd number.")

# Predict value for predict_y
thaldur_prediction = KNeighborsRegressor(n_neighbors=k, metric='minkowski', weights='distance').fit(train_x, train_y).predict(predict_x)
print("The prediction for thaldur is " + str(thaldur_prediction[0]) + ".")
# Round thaldur_prediction to integer
thaldur_prediction = round(number=thaldur_prediction[0])
print("The prediction for thaldur has been rounded to " + str(thaldur_prediction) + ".")

# Supply prediction back to appropriate patient
hungarian.loc[hungarian[impute_variable]==-9, 'thaldur'] = thaldur_prediction

# Imputing missing values (marked as -9 per data dictionary)
cols_with_missing_values = [(col, hungarian[col].value_counts()[-9]) for col in list(hungarian) if -9 in hungarian[col].unique()]
# Sort tuples by number of missing values
cols_with_missing_values.sort(key=lambda x:x[1])

# Impute rldv5
# Set y variable
impute_variable = 'rldv5'

# Obtain list of variables to use for imputation
x_variables = [x for x in list(hungarian) if x not in [x[0] for x in cols_with_missing_values] +
                        variables_not_to_use_for_imputation + ['id']]

# Select x and y variables to use - add in 'prop'
fix_rldv5 = hungarian[x_variables + [impute_variable]]

# Create list of categorical variables to one-hot encode
categorical_x_variables = ['sex', 'painloc', 'painexer', 'relrest', 'cp', 'htn', 'restecg', 'prop', 'nitr', 'pro',
                           'diuretic', 'exang', 'lvx3', 'lvx4', 'lvf']

# One-hot encode categorical variables
for value in categorical_x_variables:
    one_hot = pd.get_dummies(fix_rldv5[value], prefix=value)
    fix_rldv5 = fix_rldv5.join(one_hot)
    fix_rldv5 = fix_rldv5.drop(columns=value)

# Create list of x variables
x_variables = [x for x in list(fix_rldv5) if x != impute_variable]

# Create DataFrame with missing value(s) - will predict on
predict = fix_rldv5.loc[fix_rldv5[impute_variable]==-9]
# Set x and y predict DataFrames
predict_x, predict_y = predict[x_variables], predict[impute_variable]

# Create DataFrame to train on
train = fix_rldv5.loc[~(fix_rldv5[impute_variable]==-9)]
# Set x and y train DataFrames
train_x, train_y = train[x_variables], train[impute_variable]

# Fit scaler on train_x
train_x = scaler.fit_transform(train_x)

# Transform predict_x
predict_x = scaler.transform(predict_x)

# Obtain k (number of neighbors) by using sqrt(n)
k = round(sqrt(len(train_x)))
print(f"k is {k}.")

# Check to make sure k is odd number
if divmod(k, 2)[1] == 1:
    print("k is an odd number. Good to proceed.")
else:
    print("Need to make k an odd number.")

# Predict value for predict_y
rldv5_prediction = KNeighborsRegressor(n_neighbors=k, metric='minkowski', weights='distance').fit(train_x, train_y).predict(predict_x)
print("The prediction for rldv5 is " + str(rldv5_prediction[0]) + ".")
# Round rldv5_prediction to integer
rldv5_prediction = round(number=rldv5_prediction[0])
print("The prediction for rldv5 has been rounded to " + str(rldv5_prediction) + ".")

# Supply prediction back to appropriate patient
hungarian.loc[hungarian[impute_variable]==-9, 'rldv5'] = rldv5_prediction

# Imputing missing values (marked as -9 per data dictionary)
cols_with_missing_values = [(col, hungarian[col].value_counts()[-9]) for col in list(hungarian) if -9 in hungarian[col].unique()]
# Sort tuples by number of missing values
cols_with_missing_values.sort(key=lambda x:x[1])

# Impute met
# Set y variable
impute_variable = 'met'

# Obtain list of variables to use for imputation
x_variables = [x for x in list(hungarian) if x not in [x[0] for x in cols_with_missing_values] +
                        variables_not_to_use_for_imputation + ['id']]

# Select x and y variables to use - add in 'rldv5'
fix_met = hungarian[x_variables + [impute_variable]]

# Create list of categorical variables to one-hot encode
categorical_x_variables = ['sex', 'painloc', 'painexer', 'relrest', 'cp', 'htn', 'restecg', 'prop', 'nitr', 'pro',
                           'diuretic', 'exang', 'lvx3', 'lvx4', 'lvf']

# One-hot encode categorical variables
for value in categorical_x_variables:
    one_hot = pd.get_dummies(fix_met[value], prefix=value)
    fix_met = fix_met.join(one_hot)
    fix_met = fix_met.drop(columns=value)

# Create list of x variables
x_variables = [x for x in list(fix_met) if x != impute_variable]

# Create DataFrame with missing value(s) - will predict on
predict = fix_met.loc[fix_met[impute_variable]==-9]
# Set x and y predict DataFrames
predict_x, predict_y = predict[x_variables], predict[impute_variable]

# Create DataFrame to train on
train = fix_met.loc[~(fix_met[impute_variable]==-9)]
# Set x and y train DataFrames
train_x, train_y = train[x_variables], train[impute_variable]

# Fit scaler on train_x
train_x = scaler.fit_transform(train_x)

# Transform predict_x
predict_x = scaler.transform(predict_x)

# Obtain k (number of neighbors) by using sqrt(n)
k = round(sqrt(len(train_x)))
print(f"k is {k}.")

# Check to make sure k is odd number
if divmod(k, 2)[1] == 1:
    print("k is an odd number. Good to proceed.")
else:
    print("Need to make k an odd number.")

# Predict value for predict_y
met_prediction = KNeighborsRegressor(n_neighbors=k, metric='minkowski', weights='distance').fit(train_x, train_y).predict(predict_x)
print("The predictions for met are:")
print(met_prediction)

# Round met_prediction to integer
for i in range(len(met_prediction)):
    met_prediction[i] = round(number=met_prediction[i])
    print("The prediction for met_prediction" + "[" + str(i) + "]" + " has been rounded to " + str(met_prediction[i]) + ".")

# Supply prediction back to appropriate patient
hungarian.loc[hungarian[impute_variable]==-9, impute_variable] = met_prediction

# Imputing missing values (marked as -9 per data dictionary)
cols_with_missing_values = [(col, hungarian[col].value_counts()[-9]) for col in list(hungarian) if -9 in hungarian[col].unique()]
# Sort tuples by number of missing values
cols_with_missing_values.sort(key=lambda x:x[1])

# Impute fbs
# Set y variable
impute_variable = 'fbs'

# Obtain list of variables to use for imputation
x_variables = [x for x in list(hungarian) if x not in [x[0] for x in cols_with_missing_values] +
                        variables_not_to_use_for_imputation + ['id']]

# Select x and y variables to use - add in 'met'
fix_fbs = hungarian[x_variables + [impute_variable]]

# Create list of categorical variables to one-hot encode
categorical_x_variables = ['sex', 'painloc', 'painexer', 'relrest', 'cp', 'htn', 'restecg', 'prop', 'nitr', 'pro',
                           'diuretic', 'exang', 'lvx3', 'lvx4', 'lvf']

# One-hot encode categorical variables
for value in categorical_x_variables:
    one_hot = pd.get_dummies(fix_fbs[value], prefix=value)
    fix_fbs = fix_fbs.join(one_hot)
    fix_fbs = fix_fbs.drop(columns=value)

# Create list of x variables
x_variables = [x for x in list(fix_fbs) if x != impute_variable]

# Create DataFrame with missing value(s) - will predict on
predict = fix_fbs.loc[fix_fbs[impute_variable]==-9]
# Set x and y predict DataFrames
predict_x, predict_y = predict[x_variables], predict[impute_variable]

# Create DataFrame to train on
train = fix_fbs.loc[~(fix_fbs[impute_variable]==-9)]
# Set x and y train DataFrames
train_x, train_y = train[x_variables], train[impute_variable]

# Fit scaler on train_x
train_x = scaler.fit_transform(train_x)

# Transform predict_x
predict_x = scaler.transform(predict_x)

# Obtain k (number of neighbors) by using sqrt(n)
k = round(sqrt(len(train_x)))
print(f"k is {k}.")

# Check to make sure k is odd number
if divmod(k, 2)[1] == 1:
    print("k is an odd number. Good to proceed.")
else:
    print("Need to make k an odd number.")

# Predict value for predict_y
fbs_prediction = KNeighborsClassifier(n_neighbors=k, metric='minkowski', weights='distance').fit(train_x, train_y).predict(predict_x)
print("The predictions for fbs are:")
print(fbs_prediction)

# Supply prediction back to appropriate patient
hungarian.loc[hungarian[impute_variable]==-9, impute_variable] = fbs_prediction

# Imputing missing values (marked as -9 per data dictionary)
cols_with_missing_values = [(col, hungarian[col].value_counts()[-9]) for col in list(hungarian) if -9 in hungarian[col].unique()]
# Sort tuples by number of missing values
cols_with_missing_values.sort(key=lambda x:x[1])

# Impute fbs
# Set y variable
impute_variable = 'proto'

# Obtain list of variables to use for imputation
x_variables = [x for x in list(hungarian) if x not in [x[0] for x in cols_with_missing_values] +
                        variables_not_to_use_for_imputation + ['id']]

# Select x and y variables to use - add in 'fbs'
fix_proto = hungarian[x_variables + [impute_variable]]

# Create list of categorical variables to one-hot encode
categorical_x_variables = ['sex', 'painloc', 'painexer', 'relrest', 'cp', 'htn', 'fbs', 'restecg', 'prop', 'nitr', 'pro',
                           'diuretic', 'exang', 'lvx3', 'lvx4', 'lvf']

# One-hot encode categorical variables
for value in categorical_x_variables:
    one_hot = pd.get_dummies(fix_proto[value], prefix=value)
    fix_proto = fix_proto.join(one_hot)
    fix_proto = fix_proto.drop(columns=value)

# Create list of x variables
x_variables = [x for x in list(fix_proto) if x != impute_variable]

# Create DataFrame with missing value(s) - will predict on
predict = fix_proto.loc[fix_proto[impute_variable]==-9]
# Set x and y predict DataFrames
predict_x, predict_y = predict[x_variables], predict[impute_variable]

# Create DataFrame to train on
train = fix_proto.loc[~(fix_proto[impute_variable]==-9)]
# Set x and y train DataFrames
train_x, train_y = train[x_variables], train[impute_variable]

# Fit scaler on train_x
train_x = scaler.fit_transform(train_x)
# Transform train_x
train_x = scaler.transform(train_x)

# Transform predict_x
predict_x = scaler.transform(predict_x)

# Obtain k (number of neighbors) by using sqrt(n)
k = round(sqrt(len(train_x)))
print(f"k is {k}.")

# Check to make sure k is odd number
if divmod(k, 2)[1] == 1:
    print("k is an odd number. Good to proceed.")
else:
    print("Need to make k an odd number.")

# Predict value for predict_y
proto_prediction = KNeighborsClassifier(n_neighbors=k, metric='minkowski', weights='distance').fit(train_x, train_y).predict(predict_x)
print("The predictions for proto are:")
print(proto_prediction)

# Supply prediction back to appropriate patient
hungarian.loc[hungarian[impute_variable]==-9, impute_variable] = proto_prediction

# Imputing missing values (marked as -9 per data dictionary)
cols_with_missing_values = [(col, hungarian[col].value_counts()[-9]) for col in list(hungarian) if -9 in hungarian[col].unique()]
# Sort tuples by number of missing values
cols_with_missing_values.sort(key=lambda x:x[1])

# Impute chol
impute_variable = 'chol'

# Obtain list of variables to use for imputation
x_variables = [x for x in list(hungarian) if x not in [x[0] for x in cols_with_missing_values] +
                        variables_not_to_use_for_imputation + ['id']]

# Select x and y variables to use - add in 'fbs'
fix_chol = hungarian[x_variables + [impute_variable]]

# Create list of categorical variables to one-hot encode
categorical_x_variables = ['sex', 'painloc', 'painexer', 'relrest', 'cp', 'htn', 'fbs', 'restecg', 'prop', 'nitr', 'pro',
                           'diuretic', 'proto', 'exang', 'lvx3', 'lvx4', 'lvf']


# One-hot encode categorical variables
for value in categorical_x_variables:
    one_hot = pd.get_dummies(fix_chol[value], prefix=value)
    fix_chol = fix_chol.join(one_hot)
    fix_chol = fix_chol.drop(columns=value)

# Create list of x variables
x_variables = [x for x in list(fix_chol) if x != impute_variable]

# Create DataFrame with missing value(s) - will predict on
predict = fix_chol.loc[fix_chol[impute_variable]==-9]
# Set x and y predict DataFrames
predict_x, predict_y = predict[x_variables], predict[impute_variable]

# Create DataFrame to train on
train = fix_chol.loc[~(fix_chol[impute_variable]==-9)]
# Set x and y train DataFrames
train_x, train_y = train[x_variables], train[impute_variable]

# Fit scaler on train_x
train_x = scaler.fit_transform(train_x)

# Transform predict_x
predict_x = scaler.transform(predict_x)

# Obtain k (number of neighbors) by using sqrt(n)
k = round(sqrt(len(train_x)))
print(f"k is {k}.")

# Check to make sure k is odd number
if divmod(k, 2)[1] == 1:
    print("k is an odd number. Good to proceed.")
else:
    print("Need to make k an odd number.")
    # Substract one to make k odd number
    k -= 1
    print(f"k is now {k}.")

# Predict value for predict_y
chol_prediction = KNeighborsRegressor(n_neighbors=k, metric='minkowski', weights='distance').fit(train_x, train_y).predict(predict_x)
print("The predictions for chol are:")
print(chol_prediction)

# Round chol_prediction to integer
for i in range(0, len(chol_prediction)):
    chol_prediction[i] = round(number=chol_prediction[i])
    print(f"The prediction for chol_prediction [{str(i)}] has been rounded to {chol_prediction[i]}.")

# Supply prediction back to appropriate patient
hungarian.loc[hungarian[impute_variable]==-9, impute_variable] = chol_prediction

# Set y variable to 0-1 range (as previous studies have done)
################ Keep as is with different levels #####################################
hungarian.loc[hungarian.num > 0, "num"] = 1

### Feature engineering ###

# Create column of time between ekg and cardiac cath
# Create column of ekg dates
ekg_date = []
for year, month, day in zip(hungarian.ekgyr, hungarian.ekgmo, hungarian.ekgday):
    x = str(year) + '-' + str(month) + '-' + str(day)
    ekg_date.append(dt.datetime.strptime(x, '%y-%m-%d').strftime('%Y-%m-%d'))
# Append list to datetime to create column
hungarian['ekg_date'] = ekg_date

# Correct 2-30-86 issue (1986 was not a leap year)
hungarian.loc[(hungarian.cyr==86) & (hungarian.cmo==2) & (hungarian.cday==30), ('cmo', 'cday')] = (3,1)

cardiac_cath_date = []
for year, month, day in zip(hungarian.cyr, hungarian.cmo, hungarian.cday):
    x = str(year) + '-' + str(month) + '-' + str(day)
    print(x)
    cardiac_cath_date.append(dt.datetime.strptime(x, '%y-%m-%d').strftime('%Y-%m-%d'))
# Append list to datetime to create column
hungarian['cardiac_cath_date'] = cardiac_cath_date

# Days between cardiac cath and ekg
hungarian['days_between_c_ekg'] = (pd.to_datetime(hungarian.cardiac_cath_date) - pd.to_datetime(hungarian.ekg_date)).dt.days

### Data visualizations and statistical analysis ###

# Determine 'strong' alpha value based on sample size (AA 501, 3 - More Complex ANOVA Regression)
sample_size_one, strong_alpha_value_one = 100, 0.001
sample_size_two, strong_alpha_value_two = 1000, 0.0003
slope = (strong_alpha_value_two - strong_alpha_value_one)/(sample_size_two - sample_size_one)
strong_alpha_value = slope * (hungarian.shape[0] - sample_size_one) + strong_alpha_value_one
print(f"The alpha value for use in hypothesis tests is {strong_alpha_value}.")

### Exploratory data analysis ###

# Set aesthetic parameters
sns.set()

# List of continuous variables
continuous_variables = ['age', 'trestbps', 'chol', 'thaldur', 'met', 'thalach', 'thalrest', 'tpeakbps', 'tpeakbpd',
                        'trestbpd', 'oldpeak', 'rldv5', 'rldv5e', 'days_between_c_ekg']

# List of categorical variables
categorical_variables = ['sex', 'painloc', 'painexer', 'relrest', 'cp', 'htn', 'fbs', 'restecg', 'prop', 'nitr',
                         'pro', 'diuretic', 'proto', 'exang', 'lvx3', 'lvx4', 'lvf']

# Target variable
target_variable = 'num'

### Create PCA variable from rldv5 and rldv5e
hungarian['rldv5_rldv5e_pca'] = PCA(n_components=1).fit_transform(hungarian[['rldv5', 'rldv5e']])

# Append new PCA'd variable to continuous variable list
continuous_variables.append('rldv5_rldv5e_pca')

# Heatmap of correlations
sns.heatmap(hungarian[continuous_variables].corr())
# Correlations > 0.6
print(hungarian[continuous_variables].corr()[hungarian[continuous_variables].corr()>0.6])
# Correlations < 0.6
print(hungarian[continuous_variables].corr()[hungarian[continuous_variables].corr()<-0.6])

### Do histograms for all continuous variable splitting num (put same variable on same line)
fig, axes = plt.subplots(nrows=4, ncols=2, figsize=(28,8))
fig.subplots_adjust(hspace=0.5)
fig.suptitle('Distributions of Continuous Features')

for i, continuous in zip(range(len(axes)), continuous_variables[0:4]):
    axes[i][0].hist(hungarian.loc[hungarian.num == 0, continuous])
    axes[i][0].set(title=continuous + "_0")
    axes[i][1].hist(hungarian.loc[hungarian.num == 1, continuous])
    axes[i][1].set(title=continuous + "_1")
plt.savefig('first_four_continuous_hist.png')

fig, axes = plt.subplots(nrows=4, ncols=2, figsize=(28,8))
fig.subplots_adjust(hspace=0.5)
fig.suptitle('Distributions of Continuous Features')

for i, continuous in zip(range(len(axes)), continuous_variables[4:8]):
    axes[i][0].hist(hungarian.loc[hungarian.num == 0, continuous])
    axes[i][0].set(title=continuous + "_0")
    axes[i][1].hist(hungarian.loc[hungarian.num == 1, continuous])
    axes[i][1].set(title=continuous + "_1")
plt.savefig('next_four_continuous_hist.png')

fig, axes = plt.subplots(nrows=5, ncols=2, figsize=(28,8))
fig.subplots_adjust(hspace=0.5)
fig.suptitle('Distributions of Continuous Features')

for i, continuous in zip(range(len(axes)), continuous_variables[8:13]):
    axes[i][0].hist(hungarian.loc[hungarian.num == 0, continuous])
    axes[i][0].set(title=continuous + "_0")
    axes[i][1].hist(hungarian.loc[hungarian.num == 1, continuous])
    axes[i][1].set(title=continuous + "_1")
plt.savefig('last_five_continuous_hist.png')



fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(28,8))
fig.subplots_adjust(hspace=0.5)
fig.suptitle('Distributions of Continuous Features')
for ax, continuous in zip(axes.flatten(), continuous_variables[0:4]):
    for num_value in hungarian.num.unique():
        ax.hist(hungarian.loc[hungarian.num == num_value, continuous], alpha=0.7, label=num_value)
        ax.set(title=continuous)
handles, legends = ax.get_legend_handles_labels()
fig.legend(handles, legends, loc='upper left')
plt.savefig('first_four_together_continuous_hist.png')

fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(28,8))
fig.subplots_adjust(hspace=0.5)
fig.suptitle('Distributions of Continuous Features')
for ax, continuous in zip(axes.flatten(), continuous_variables[4:8]):
    for num_value in hungarian.num.unique():
        ax.hist(hungarian.loc[hungarian.num == num_value, continuous], alpha=0.7, label=num_value)
        ax.set(title=continuous)
handles, legends = ax.get_legend_handles_labels()
fig.legend(handles, legends, loc='upper left')
plt.savefig('second_four_together_continuous_hist.png')

fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(28,8))
fig.subplots_adjust(hspace=0.5)
fig.suptitle('Distributions of Continuous Features')
for ax, continuous in zip(axes.flatten(), continuous_variables[8:]):
    for num_value in hungarian.num.unique():
        ax.hist(hungarian.loc[hungarian.num == num_value, continuous], alpha=0.7, label=num_value)
        ax.set(title=continuous)
handles, legends = ax.get_legend_handles_labels()
fig.legend(handles, legends, loc='upper left')
plt.savefig('second_four_together_continuous_hist.png')

### Check normality of continuous variables
for continuous in continuous_variables:
    print(continuous)
    print(f"Kurtosis value: {stats.kurtosis(a=hungarian[continuous], fisher=True)}")
    print(f"Sknewness value: {stats.skew(a=hungarian[continuous])}")
    print(f"P-value from normal test: {stats.normaltest(a=hungarian[continuous])[1]}")
    if stats.normaltest(a=hungarian[continuous])[1] < strong_alpha_value:
        print("Reject null hypothesis the samples comes from a normal distribution.")
        print("-------------------------------------------------------------------")
        try:
            print(f"Kurtosis value: {stats.kurtosis(a=stats.boxcox(x=hungarian[continuous])[0], fisher=True)}")
            print(f"Sknewness value: {stats.skew(a=stats.boxcox(x=hungarian[continuous])[0])}")
            print(f"P-value from normal test: {stats.normaltest(a=stats.boxcox(x=hungarian[continuous])[0])[1]}")
        except ValueError as a:
            if str(a) == "Data must be positive.":
                print(f"{continuous} contains zero or negative values.")
    else:
        print("Do not reject the null hypothesis")
    print('\n')

# Compare original distribution with boxcox'd distribution for specific variables
plt.figure()
sns.distplot(hungarian.chol)
plt.figure()
sns.distplot(stats.boxcox(x=hungarian.chol)[0]).set_title('boxcox')

# Plot original and boxcox'd distributions to each other and against num
print(len([x for x in list(hungarian) if 'boxcox' in x]))
# Create list of variables to plot for inspection
variables_for_inspection = ['chol', 'chol_boxcox', 'thalrest', 'thalrest_boxcox', 'trestbps', 'trestbps_boxcox']
fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(28,8))
fig.subplots_adjust(hspace=0.5)
fig.suptitle("Distributions of Continuous Features and their BoxCox'd Features")
for ax, variable in zip(axes.flatten(), variables_for_inspection):
    for num_value in hungarian.num.unique():
        ax.hist(hungarian.loc[hungarian.num == num_value, variable], alpha=0.7, label=num_value)
        ax.set(title=variable)
handles, legends = ax.get_legend_handles_labels()
fig.legend(handles, legends, loc='upper left')
plt.savefig('continuous_with_boxcox_hist.png')

# Add boxcox'd variables to continuous_variables list
continuous_variables.extend([x for x in list(hungarian) if 'boxcox' in x])

# Correlations > 0.6
print(hungarian[continuous_variables].corr()[hungarian[continuous_variables].corr() > 0.6])
# Correlations > 0.6 and < 1.0, drop all null columns
hungarian[continuous_variables].corr()[(hungarian[continuous_variables].corr() > 0.6) &
                                       (hungarian[continuous_variables].corr() < 1.0)].dropna(axis=1, how='all')

# Pearson chi-square tests
chi_square_analysis_list = []
for categorical in categorical_variables:
    chi, p, dof, expected = stats.chi2_contingency(pd.crosstab(index=hungarian[categorical], columns=hungarian[target_variable]))
    print(f"The chi-square value for {categorical} and {target_variable} is {chi}, and the p-value is" f" {p}, respectfully.")
    chi_square_analysis_list.append([categorical, target_variable, chi, p])

# Create DataFrame from lists of lists
chi_square_analysis_df = pd.DataFrame(chi_square_analysis_list, columns=['variable', 'target', 'chi',
                                                            'p_value']).sort_values(by='p_value', ascending=True)
# Determine categorical variables that reject null
chi_square_analysis_df.loc[chi_square_analysis_df.p_value <= strong_alpha_value]



# Boxcox necessary variables
hungarian['trestbps_boxcox'] = stats.boxcox(x=hungarian.trestbps)[0]
hungarian['chol_boxcox'] = stats.boxcox(x=hungarian.chol)[0]
hungarian['thalrest_boxcox'] = stats.boxcox(x=hungarian.thalrest)[0]

############## Plot results form each model run on ROC Curve to better observe best cut-off value ######################
# Create copy of hungarian for regression modeling
model = hungarian.copy()
# Drop columns
model = model.drop(columns=['id', 'chol', 'thalrest', 'trestbps', 'ekgyr', 'ekgmo', 'ekgday', 'cyr', 'cmo', 'cday',
                            'ekg_date', 'cardiac_cath_date', 'rldv5', 'lvx3', 'lvx4', 'lvf', 'pro', 'proto',
                            'rldv5_rldv5e_pca'])
# Dummy variable categorical variables
model = pd.get_dummies(data=model, columns=categorical_variables[:-7] + [categorical_variables[-6]] + [categorical_variables[-4]], drop_first=True)
# Create target variable
y = model['num']
# Create feature variables
x = model.drop(columns='num')

# Obtain recursive feature elimination values for all solvers and get average
# (not sure what to do about ConvergenceWarning - get warning but also get result for each solver)
rfe_logit = pd.DataFrame(data=list(x), columns=['variable'])
for solve in ['liblinear', 'newton-cg', 'lbfgs', 'sag', 'saga']:
    rfe_logit = rfe_logit.merge(pd.DataFrame(data=[list(x), RFE(LogisticRegression(solver=solve, max_iter=100),
                n_features_to_select=1).fit(x, y).ranking_.tolist()]).T.rename(columns={0: 'variable', 1:
                'rfe_ranking_' + solve}), on='variable')
# Get average ranking for each variable
rfe_logit['rfe_ranking_avg'] = rfe_logit[['rfe_ranking_liblinear', 'rfe_ranking_newton-cg', 'rfe_ranking_lbfgs',
                                          'rfe_ranking_sag', 'rfe_ranking_saga']].mean(axis=1)
# Sort DataFrame
rfe_logit = rfe_logit.sort_values(by='rfe_ranking_avg', ascending=True).reset_index(drop=True)

# Train/test split
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.33, random_state=43)
# Run models - start at top and add variables with each iteration

# Test 'weaker' alpha value
strong_alpha_value = 0.04
model_search_logit = []
logit_variable_list = []
insignificant_variables_list = []
for i in range(len(rfe_logit)):
    if rfe_logit['variable'][i] not in logit_variable_list and rfe_logit['variable'][i] not in insignificant_variables_list:
        logit_variable_list.extend([rfe_logit['variable'][i]])
        # logit_variable_list = list(set(logit_variable_list).difference(set(insignificant_variables_list)))
        logit_variable_list = [x for x in logit_variable_list if x not in insignificant_variables_list]
        print(logit_variable_list)
        # Add related one-hot encoded variables if variable is categorical
        if logit_variable_list[-1].split('_')[-1] in sorted([x for x in list(set([x.split('_')[-1] for x in list(x)])) if len(x) == 1]):
            logit_variable_list.extend([var for var in list(x) if logit_variable_list[-1].split('_')[0] in var and var != logit_variable_list[-1]])
            print(logit_variable_list)
        # Build logistic regression
        sm_logistic = sm.Logit(y_train, x_train[logit_variable_list]).fit()
        # All p-values are significant
        if all(p_values < strong_alpha_value for p_values in sm_logistic.summary2().tables[1]._getitem_column("P>|z|").values):
            print("-----------")
            print((sm_logistic.summary2().tables[1]._getitem_column("P>|z|").index.tolist(),
                                     sm_logistic.summary2().tables[1]._getitem_column("P>|z|").values.tolist()))
            print("-----------")
            print("-----------")
            model_search_logit.append([(sm_logistic.summary2().tables[0][0][6], sm_logistic.summary2().tables[0][1][6]),
                                    (sm_logistic.summary2().tables[0][2][0], sm_logistic.summary2().tables[0][3][0]),
                                    (sm_logistic.summary2().tables[0][2][1], sm_logistic.summary2().tables[0][3][1]),
                                    (sm_logistic.summary2().tables[0][2][2], sm_logistic.summary2().tables[0][3][2]),
                                    (sm_logistic.summary2().tables[0][2][3], sm_logistic.summary2().tables[0][3][3]),
                                    (sm_logistic.summary2().tables[0][2][4], sm_logistic.summary2().tables[0][3][4]),
                                    (sm_logistic.summary2().tables[0][2][5], sm_logistic.summary2().tables[0][3][5]),
                                    (sm_logistic.summary2().tables[1]._getitem_column("P>|z|").index.tolist(),
                                     sm_logistic.summary2().tables[1]._getitem_column("P>|z|").values.tolist())])
        # P-value(s) of particular variable(s) is not significant
        elif any(p_values > strong_alpha_value for p_values in sm_logistic.summary2().tables[1]._getitem_column("P>|z|").values):
            print('*********')
            print(logit_variable_list[-1])
            print('*********')
            if logit_variable_list[-1].split('_')[-1] in sorted([x for x in list(set([x.split('_')[-1] for x in list(x)])) if len(x) == 1]):
                cat_var_level_check = sm_logistic.summary2().tables[1]._getitem_column("P>|z|")[sm_logistic.summary2().
                    tables[1]._getitem_column("P>|z|").index.isin([var for var in list(x) if
                                                                   logit_variable_list[-1].split('_')[0] in var])]
                # If True, at least one level of the categorical variable is significant so keep all levels of variable
                if any(p_values < strong_alpha_value for p_values in cat_var_level_check.values):
                    model_search_logit.append([(sm_logistic.summary2().tables[0][0][6], sm_logistic.summary2().tables[0][1][6]),
                                    (sm_logistic.summary2().tables[0][2][0], sm_logistic.summary2().tables[0][3][0]),
                                    (sm_logistic.summary2().tables[0][2][1], sm_logistic.summary2().tables[0][3][1]),
                                    (sm_logistic.summary2().tables[0][2][2], sm_logistic.summary2().tables[0][3][2]),
                                    (sm_logistic.summary2().tables[0][2][3], sm_logistic.summary2().tables[0][3][3]),
                                    (sm_logistic.summary2().tables[0][2][4], sm_logistic.summary2().tables[0][3][4]),
                                    (sm_logistic.summary2().tables[0][2][5], sm_logistic.summary2().tables[0][3][5]),
                                    (sm_logistic.summary2().tables[1]._getitem_column("P>|z|").index.tolist(),
                                     sm_logistic.summary2().tables[1]._getitem_column("P>|z|").values.tolist())])
                # Else False - remove all levels of categorical variable
                else:
                    print("!!!!!!!!!!!!!!!!!!!!!")
                    print(sm_logistic.summary2())
                    insignificant_variables_list.extend(cat_var_level_check.index)
            else:
                print('&&&&&&&&&&&&&')
                print(sm_logistic.summary2())
                print(logit_variable_list[-1])
                cont_var_check = sm_logistic.summary2().tables[1]._getitem_column("P>|z|")[sm_logistic.summary2().
                    tables[1]._getitem_column("P>|z|").index.isin([logit_variable_list[-1]])]
                # Continuous variable is significant
                if cont_var_check.values[0] < strong_alpha_value:
                    model_search_logit.append([(sm_logistic.summary2().tables[0][0][6], sm_logistic.summary2().tables[0][1][6]),
                                    (sm_logistic.summary2().tables[0][2][0], sm_logistic.summary2().tables[0][3][0]),
                                    (sm_logistic.summary2().tables[0][2][1], sm_logistic.summary2().tables[0][3][1]),
                                    (sm_logistic.summary2().tables[0][2][2], sm_logistic.summary2().tables[0][3][2]),
                                    (sm_logistic.summary2().tables[0][2][3], sm_logistic.summary2().tables[0][3][3]),
                                    (sm_logistic.summary2().tables[0][2][4], sm_logistic.summary2().tables[0][3][4]),
                                    (sm_logistic.summary2().tables[0][2][5], sm_logistic.summary2().tables[0][3][5]),
                                    (sm_logistic.summary2().tables[1]._getitem_column("P>|z|").index.tolist(),
                                     sm_logistic.summary2().tables[1]._getitem_column("P>|z|").values.tolist())])
                else:
                    print('^^^^^^^^^^^^^')
                    print(logit_variable_list[-1])
                    insignificant_variables_list.append(logit_variable_list[-1])
# Create DataFrame of logisitic regression results
model_search_logit = pd.DataFrame(model_search_logit, columns = ['converged', 'pseudo_r_squared', 'aic', 'bic',
                                            'log_likelihood', 'll_null', 'llr_p_value', 'columns_significance'])
model_results_logit = []
for solve in ['liblinear', 'newton-cg', 'lbfgs', 'sag', 'saga']:
    for col in model_search_logit['columns_significance']:
        print(solve, col[0])
        try:
            logit_predict = cross_val_predict(LogisticRegression(solver=solve, max_iter=100), x[col[0]], y, cv=5)
            print(confusion_matrix(y_true=y, y_pred=logit_predict))
            conf_matr = confusion_matrix(y_true=y, y_pred=logit_predict)
            model_results_logit.append([solve, col[0], conf_matr[0][0], conf_matr[0][1], conf_matr[1][0], conf_matr[1][1]])
        except ConvergenceWarning:
            print("#############")
# Create DataFrame of results
model_results_logit = pd.DataFrame(model_results_logit, columns = ['solver', 'cols', 'true_negatives', 'false_positives',
                                             'false_negatives', 'true_positives'])
# Create recall, precision, and f1-score columns
model_results_logit['recall'] = model_results_logit.true_positives/(model_results_logit.true_positives + model_results_logit.false_negatives)
model_results_logit['precision'] = model_results_logit.true_positives/(model_results_logit.true_positives + model_results_logit.false_positives)
model_results_logit['f1_score'] = 2 * (model_results_logit.precision * model_results_logit.recall) / (model_results_logit.precision + model_results_logit.recall)
# Sort DataFrame
model_results_logit = model_results_logit.sort_values(by=['f1_score'], ascending=False)
print(model_results_logit)

if len(model_results_logit.loc[model_results_logit.f1_score==model_results_logit.f1_score.max()]) > 1:
    top_model_result_logit = model_results_logit.loc[(model_results_logit.f1_score == model_results_logit.f1_score.max()) &
        (model_results_logit['cols'].apply(len) == min(map(lambda x: len(x[[1]][0]),
        model_results_logit.loc[model_results_logit.f1_score==model_results_logit.f1_score.max()].values)))].sample(n=1)


# # Create all possible feature combinations for regression
# variable_combinations = []
# for length in range(1, len(list(x)[:-15] + list(set([var.split("_")[0] for var in list(x)[-15:]])))+1):
#     for subset in itertools.combinations(list(x)[:-15] + list(set([var.split("_")[0] for var in list(x)[-15:]])), length):
#         variable_combinations.append(list(subset))

# # Create dict of original and dummified categorical variables
# orig_dummied_dict = {}
# for original in categorical_variables[:-7] + [categorical_variables[-6]] + [categorical_variables[-4]]:
#     orig_dummied_dict[original] = [dummied for dummied in list(x) if original in dummied]
#
# ### Update variable_combinations to have correct form of categorical variable (i.e. dummified version)
# ### Build models for all variable combinatons
# # Empty list to append results to
# model_search_list_logit = []
# for var_com in variable_combinations:
#     print(var_com)
#     print('--------')
#     if any([i in orig_dummied_dict for i in var_com]):
#         for i, v in orig_dummied_dict.items():
#             if i in var_com:
#                 var_com.remove(i)
#                 var_com.extend(v)
#         # Train/test split
#         x_train, x_test, y_train, y_test = train_test_split(x[var_com], y, test_size=0.33, random_state=43)
#         print(var_com)
#         print("*********")
#         # Build logistic regression
#         sm_logistic = sm.Logit(y_train, x_train[var_com]).fit()
#         model_search_list_logit.append([(sm_logistic.summary2().tables[0][0][6], sm_logistic.summary2().tables[0][1][6]),
#                                         (sm_logistic.summary2().tables[0][2][0], sm_logistic.summary2().tables[0][3][0]),
#                                         (sm_logistic.summary2().tables[0][2][1], sm_logistic.summary2().tables[0][3][1]),
#                                         (sm_logistic.summary2().tables[0][2][2], sm_logistic.summary2().tables[0][3][2]),
#                                         (sm_logistic.summary2().tables[0][2][3], sm_logistic.summary2().tables[0][3][3]),
#                                         (sm_logistic.summary2().tables[0][2][4], sm_logistic.summary2().tables[0][3][4]),
#                                         (sm_logistic.summary2().tables[0][2][5], sm_logistic.summary2().tables[0][3][5]),
#                                         (sm_logistic.summary2().tables[1]._getitem_column("P>|z|").index.tolist(),
#                                          sm_logistic.summary2().tables[1]._getitem_column("P>|z|").values.tolist())])
#     else:
#         # Train/test split
#         x_train, x_test, y_train, y_test = train_test_split(x[var_com], y, test_size=0.33, random_state=43)
#         print(var_com)
#         print("==========")
#         # Build logistic regression
#         sm_logistic = sm.Logit(y_train, x_train[var_com]).fit()
#         model_search_list_logit.append([(sm_logistic.summary2().tables[0][0][6], sm_logistic.summary2().tables[0][1][6]),
#                                         (sm_logistic.summary2().tables[0][2][0], sm_logistic.summary2().tables[0][3][0]),
#                                         (sm_logistic.summary2().tables[0][2][1], sm_logistic.summary2().tables[0][3][1]),
#                                         (sm_logistic.summary2().tables[0][2][2], sm_logistic.summary2().tables[0][3][2]),
#                                         (sm_logistic.summary2().tables[0][2][3], sm_logistic.summary2().tables[0][3][3]),
#                                         (sm_logistic.summary2().tables[0][2][4], sm_logistic.summary2().tables[0][3][4]),
#                                         (sm_logistic.summary2().tables[0][2][5], sm_logistic.summary2().tables[0][3][5]),
#                                         (sm_logistic.summary2().tables[1]._getitem_column("P>|z|").index.tolist(),
#                                          sm_logistic.summary2().tables[1]._getitem_column("P>|z|").values.tolist())])

from sklearn.metrics import roc_auc_score
from sklearn.metrics import roc_curve
logit_roc_auc = roc_auc_score(y_test, logistic_regression_model.fit(x_train[['exang_1', 'cp_2', 'cp_3', 'cp_4', 'oldpeak']],
                y_train).predict(x_test[['exang_1', 'cp_2', 'cp_3', 'cp_4', 'oldpeak']]))
fpr, tpr, thresholds = roc_curve(y_test, logistic_regression_model.fit(x_train[['exang_1', 'cp_2', 'cp_3', 'cp_4', 'oldpeak']],
                y_train).predict_proba(x_test[['exang_1', 'cp_2', 'cp_3', 'cp_4', 'oldpeak']])[:,1])
# Create DataFrame of results
roc_curve_df = pd.DataFrame([fpr, tpr, thresholds]).T
# Rename columns
roc_curve_df = roc_curve_df.rename(columns={0: 'fpr', 1: 'tpr', 2: 'thresholds'})

# ROC Curve plot
plt.figure()
plt.plot(fpr, tpr, label='Logistic Regression (area = %0.2f)' % logit_roc_auc)
plt.plot([0, 1], [0, 1],'r--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver operating characteristic')
plt.legend(loc="lower right")

### Next steps: feature enginering (age/ekgyr)
# Drop ek- and c- columns?
# Drop lvx- and lvf?

# Determine optimal value for threshold (# tpr - (1-fpr) is zero or near to zero is the optimal cut off point)
i = np.arange(len(tpr))
roc = pd.DataFrame({'tf' : pd.Series(tpr-(1-fpr), index=i), 'threshold' : pd.Series(thresholds, index=i)})
roc_t = roc.iloc[(roc.tf-0).abs().argsort()[:1]]
list(roc_t['threshold'])

# Want high sensitivity (want to miss as few 1 patients as possible and okay to miss on a few extra 0 patients)
# The "missed" 0's could be potential 1's in the future if conditions for them worsen
# Optimal cut-off value from this -> fpr = 0.229508  tpr = 0.861111  threshold = 0.402949
# DataFrame of roc curve values
roc_curve_df = pd.DataFrame([fpr, tpr, thresholds]).T
# Rename columns
roc_curve_df = roc_curve_df.rename(columns={0: 'fpr', 1: 'tpr', 2: 'thresholds'})

logistic_regression_predict = cross_val_predict(logistic_regression_model,
                              x[['exang_1', 'cp_2', 'cp_3', 'cp_4', 'oldpeak']], y, cv=5, method='predict_proba')[:,1].tolist()
logistic_regression_predict = [1 if x >= list(roc_t['threshold'])[0] else 0 for x in logistic_regression_predict]

# Create DataFrame of model predictions from all models
model_results = pd.DataFrame()
# Logistic Regression prediction
model_results['logistic_regression_prediction'] = logistic_regression_predict






# Create copy of hungarian for non-regression modeling
model = hungarian.copy()
# Drop columns
model = model.drop(columns=['id', 'chol', 'thalrest', 'trestbps', 'ekgyr', 'ekgmo', 'ekgday', 'cyr', 'cmo', 'cday',
                            'ekg_date', 'cardiac_cath_date', 'rldv5', 'lvx3', 'lvx4', 'lvf', 'pro', 'proto',
                            'rldv5_rldv5e_pca'])
# Dummy variable categorical variables
model = pd.get_dummies(data=model, columns=categorical_variables[:-7] + [categorical_variables[-6]] + [categorical_variables[-4]], drop_first=False)
# Create target variable
y = model['num']
# Create feature variables
x = model.drop(columns='num')

### Random forest classifer ###
### Can create ensemble models using different training sets (bagging)

# Define parameters of Random Forest Classifier
random_forest_model = RandomForestClassifier(random_state=1)
# Define parameters for grid search
param_grid = {'n_estimators': np.arange(10, 111, step=5), 'criterion': ['gini', 'entropy'],
              'max_features': np.arange(2, 27, step=3)}
cv = ShuffleSplit(n_splits=5, test_size=0.3)

# Define grid search CV parameters
grid_search = GridSearchCV(random_forest_model, param_grid, cv=cv) # , scoring='recall' # warm_start=True
# Loop to iterate through least important variables according to random_forest_feature_importance and grid search
x_all = list(x)
model_search_rfc = []
while True:
    grid_search.fit(x, y)
    print(f'Best parameters for current grid seach: {grid_search.best_params_}')
    print(f'Best score for current grid seach: {grid_search.best_score_}')
    # print(grid_search.best_params_, grid_search.best_score_) # {'criterion': 'entropy', 'max_features': 7, 'n_estimators': 15} 0.8409090909090909
    # Define parameters of Random Forest Classifier from grid search
    random_forest_model = RandomForestClassifier(criterion=grid_search.best_params_['criterion'],
                                                 max_features=grid_search.best_params_['max_features'],
                                                 n_estimators=grid_search.best_params_['n_estimators'],
                                                 random_state=1)
    # Cross-validate and predict using Random Forest Classifer
    random_forest_predict = cross_val_predict(random_forest_model, x, y, cv=5)
    print(confusion_matrix(y_true=y, y_pred=random_forest_predict))
    conf_matr = confusion_matrix(y_true=y, y_pred=random_forest_predict)
    model_search_rfc.append([grid_search.best_params_, grid_search.best_score_, conf_matr[0][0], conf_matr[0][1],
                             conf_matr[1][0], conf_matr[1][1], set(x_all).difference(x)])
    # Run random forest with parameters from grid search to obtain feature importances
    random_forest_feature_importance = pd.DataFrame(data=[list(x),
                RandomForestClassifier(criterion=grid_search.best_params_['criterion'],
                 max_features=grid_search.best_params_['max_features'],
                 n_estimators=grid_search.best_params_['n_estimators'], random_state=1).fit(x,y).feature_importances_.tolist()]).T.rename(columns={0:'variable',
                 1:'importance'}).sort_values(by='importance', ascending=False)
    print(random_forest_feature_importance)
    if len(random_forest_feature_importance.loc[random_forest_feature_importance.importance<0.01]) > 0:
        for i in range(1, len(random_forest_feature_importance.loc[random_forest_feature_importance.importance<0.01])+1):
            print(f"'Worst' variable being examined: {random_forest_feature_importance.loc[random_forest_feature_importance.importance<0.01].variable.values[-i]}")
            bottom_variable = random_forest_feature_importance.loc[random_forest_feature_importance.importance<0.01].variable.values[-i]
            bottom_variable = bottom_variable.split('_')[0]
            bottom_variable = [col for col in list(x) if bottom_variable in col]
            compare_counter = 0
            for var in bottom_variable:
                if var in random_forest_feature_importance.loc[random_forest_feature_importance.importance<0.01].variable.values:
                    compare_counter += 1
            if len(bottom_variable) == compare_counter:
                print(f"Following variable(s) will be dropped from x {bottom_variable}")
                x = x.drop(columns=bottom_variable)
                break
            else:
                print("Next 'worst' variable will be examined for dropping.")
                continue
        else:
            break
# Create DataFrame of random forest classifer results
model_search_rfc = pd.DataFrame(model_search_rfc, columns=['best_model_params_grid_search', 'best_score_grid_search',
                                             'true_negatives', 'false_positives',
                                             'false_negatives', 'true_positives', 'variables_not_used'])
# Create recall and precision columns
model_search_rfc['recall'] = model_search_rfc.true_positives/(model_search_rfc.true_positives + model_search_rfc.false_negatives)
model_search_rfc['precision'] = model_search_rfc.true_positives/(model_search_rfc.true_positives + model_search_rfc.false_positives)
model_search_rfc['f1_score'] = 2 * (model_search_rfc.precision * model_search_rfc.recall) / (model_search_rfc.precision + model_search_rfc.recall)
# Sort DataFrame
model_search_rfc = model_search_rfc.sort_values(by=['f1_score'], ascending=False)


if len(model_search_rfc.loc[model_search_rfc.f1_score==model_search_rfc.f1_score.max()]) > 1:
    print("Fix multiple best model problem for rfc")
else:
    top_model_result_rfc = model_search_rfc.loc[model_search_rfc.f1_score==model_search_rfc.f1_score.max()]













### Support-vector machine classifer
# Standard scale continuous variables
scaler = StandardScaler()

# Create copy of x for standard scaling
x_std = x.copy()

x_std.loc[:, 'age':'days_between_c_ekg'] = scaler.fit_transform(x_std.loc[:, 'age':'days_between_c_ekg'])

# Define parameters of SVC
svc_model = SVC(kernel='linear')
# Recursive feature elimination
rfe_svc = pd.DataFrame(data=[list(x_std), RFE(svc_model, n_features_to_select=1).fit(x_std, y).ranking_.tolist()]).T.\
    rename(columns={0: 'variable', 1: 'rfe_ranking'}).sort_values(by='rfe_ranking').reset_index(drop=True)

svc_model = SVC(random_state=1)
param_grid = {'kernel': ['rbf', 'sigmoid', 'linear'], 'C': np.arange(0.10, 2.41, step=0.1), 'gamma': ['scale', 'auto']}
cv = ShuffleSplit(n_splits=5, test_size=0.3)
# Define grid search CV parameters
grid_search = GridSearchCV(svc_model, param_grid, cv=cv) # , scoring='recall'

# Loop through features based on recursive feature elimination evaluation - top to bottom
model_search_svc = []
svc_variable_list = []
for i in range(len(rfe_svc)):
    if rfe_svc['variable'][i] not in svc_variable_list:
        svc_variable_list.extend([rfe_svc['variable'][i]])
        # Add related one-hot encoded variables if variable is categorical
        if svc_variable_list[-1].split('_')[-1] in sorted([x for x in list(set([x.split('_')[-1] for x in list(x_std)])) if len(x) == 1]):
            svc_variable_list.extend([var for var in list(x_std) if svc_variable_list[-1].split('_')[0] in var and var != svc_variable_list[-1]])
        ###################################################################
        print(svc_variable_list)
        grid_search.fit(x_std[svc_variable_list], y)
        print(f'Best parameters for current grid seach: {grid_search.best_params_}')
        print(f'Best score for current grid seach: {grid_search.best_score_}')
        # Define parameters of Support-vector machine classifer from grid search
        svc_model = SVC(kernel=grid_search.best_params_['kernel'], C=grid_search.best_params_['C'],
                        gamma=grid_search.best_params_['gamma'], random_state=1)
        # Cross-validate and predict using Support-vector machine classifer
        svc_predict = cross_val_predict(svc_model, x_std[svc_variable_list], y, cv=5)
        print(confusion_matrix(y_true=y, y_pred=svc_predict))
        conf_matr = confusion_matrix(y_true=y, y_pred=svc_predict)
        model_search_svc.append([grid_search.best_params_, grid_search.best_score_, conf_matr[0][0],
                                 conf_matr[0][1], conf_matr[1][0], conf_matr[1][1], list(x_std[svc_variable_list])])
        # else:
        #     print(svc_variable_list)
        #     grid_search.fit(x_std[svc_variable_list], y)
        #     print(f'Best parameters for current grid seach: {grid_search.best_params_}')
        #     print(f'Best score for current grid seach: {grid_search.best_score_}')
        #     # Define parameters of Support-vector machine classifer from grid search
        #     svc_model = SVC(kernel=grid_search.best_params_['kernel'], C=grid_search.best_params_['C'],
        #                     gamma=grid_search.best_params_['gamma'], random_state=1)
        #     # Cross-validate and predict using Support-vector machine classifer
        #     svc_predict = cross_val_predict(svc_model, x_std[svc_variable_list], y, cv=5)
        #     print(confusion_matrix(y_true=y, y_pred=svc_predict))
        #     conf_matr = confusion_matrix(y_true=y, y_pred=svc_predict)
        #     model_search_svc.append([grid_search.best_params_, grid_search.best_score_, conf_matr[0][0],
        #                              conf_matr[0][1], conf_matr[1][0], conf_matr[1][1], list(x_std[svc_variable_list])])
# Create DataFrame of k-nearest neighbors results
model_search_svc = pd.DataFrame(model_search_svc, columns=['best_model_params_grid_search', 'best_score_grid_search',
                                             'true_negatives', 'false_positives',
                                             'false_negatives', 'true_positives', 'variables_used'])
# Create recall, precision, f1-score columns
model_search_svc['recall'] = model_search_svc.true_positives/(model_search_svc.true_positives + model_search_svc.false_negatives)
model_search_svc['precision'] = model_search_svc.true_positives/(model_search_svc.true_positives + model_search_svc.false_positives)
model_search_svc['f1_score'] = 2 * (model_search_svc.precision * model_search_svc.recall) / (model_search_svc.precision + model_search_svc.recall)
# Sort DataFrame
model_search_svc = model_search_svc.sort_values(by=['f1_score'], ascending=False)
print(model_search_svc)

# Choose top model from svc model search
if len(model_search_svc.loc[model_search_svc.f1_score==model_search_svc.f1_score.max()]) > 1:
    top_model_result_svc = model_search_svc.loc[(model_search_svc.f1_score == model_search_svc.f1_score.max()) &
        (model_search_svc['variables_used'].apply(len) == min(map(lambda x: len(x[list(model_search_svc).index('variables_used')]),
         model_search_svc.loc[model_search_svc.f1_score==model_search_svc.f1_score.max()].values)))]
    if len(top_model_result_svc) > 1:
        top_model_result_svc = top_model_result_svc.loc[top_model_result_svc.best_score_grid_search == top_model_result_svc.best_score_grid_search.max()]








svc_model = SVC(kernel='rbf', C=1.1, gamma='scale')
svc_predict = cross_val_predict(svc_model, x_std, y, cv=5)
print(confusion_matrix(y_true=y, y_pred=svc_predict))

### K-Nearest Neighbors

# Use Recursive Feature Elimination from SVC
# Define parameters of SVC
svc_model = SVC(kernel='linear', random_state=1)
# Feature importance DataFrame
feature_info = pd.DataFrame(data=[list(x_std), RFE(svc_model, n_features_to_select=1).fit(x_std, y).ranking_.tolist()]).T.\
    rename(columns={0: 'variable', 1: 'rfe_svc'}).reset_index(drop=True)

# Define parameters of Random Forest Classifier
random_forest_model = RandomForestClassifier(random_state=1)
# Merge feature importances from random forest classifer on feature_info
feature_info = feature_info.merge(pd.DataFrame(data=[list(x), random_forest_model.fit(x,y).feature_importances_.tolist()]).T.\
    rename(columns={0: 'variable', 1: 'feature_importance_rfc'}), on='variable')
# Sort values by descending random forest classifier feature importance to create ranking column
feature_info = feature_info.sort_values(by='feature_importance_rfc', ascending=False)
feature_info['feature_importance_rfc_ranking'] = np.arange(1,len(feature_info)+1)

# Define parameters of Gradient Boosting Classifier
gbm_model = GradientBoostingClassifier(random_state=1)
# Merge feature importances from gradient boosting classifer on feature_info
feature_info = feature_info.merge(pd.DataFrame(data=[list(x), gbm_model.fit(x,y).feature_importances_.tolist()]).T.\
    rename(columns={0: 'variable', 1: 'feature_importance_gbm'}), on='variable')
# Sort values by descending gradient boosting classifier feature importance to create ranking column
feature_info = feature_info.sort_values(by='feature_importance_gbm', ascending=False)
feature_info['feature_importance_gbm_ranking'] = np.arange(1,len(feature_info)+1)

# Get average of three RFE/feature importance columns
feature_info['feature_importance_avg'] = feature_info[['rfe_svc', 'feature_importance_rfc_ranking', 'feature_importance_gbm_ranking']].mean(axis=1)
# Sort values by average column
feature_info = feature_info.sort_values(by='feature_importance_avg', ascending=True).reset_index(drop=True)

# Define parameters of kNN model
knn_model = KNeighborsClassifier(metric='minkowski')
# Define parameters of grid search
param_grid = {'n_neighbors': np.arange(9, 47, step=2), 'weights': ['uniform', 'distance']}
# Define parameters of shuffle split
cv = ShuffleSplit(n_splits=5, test_size=0.3)

# Define grid search CV parameters
grid_search = GridSearchCV(knn_model, param_grid, cv=cv) # , scoring='recall'

# Append model results to this list
model_search_knn = []
# Begin top to bottom process - looking at most important variables (by RFE ranking first and adding on)
knn_variable_list = []
for i in range(len(feature_info)):
    if feature_info['variable'][i] not in knn_variable_list:
        knn_variable_list.extend([feature_info['variable'][i]])
        # Add related one-hot encoded variables if variable is categorical
        if knn_variable_list[-1].split('_')[-1] in sorted([x for x in list(set([x.split('_')[-1] for x in list(x_std)])) if len(x) == 1]):
            knn_variable_list.extend([var for var in list(x_std) if knn_variable_list[-1].split('_')[0] in var and var != knn_variable_list[-1]])
        print(knn_variable_list)
        grid_search.fit(x_std[knn_variable_list], y)
        print(f'Best parameters for current grid seach: {grid_search.best_params_}')
        print(f'Best score for current grid seach: {grid_search.best_score_}')
        # Define parameters of k-nearest neighbors from grid search
        knn_model = KNeighborsClassifier(metric='minkowski', n_neighbors=grid_search.best_params_['n_neighbors'],
                        weights=grid_search.best_params_['weights'])
        # Cross-validate and predict using Support-vector machine classifer
        knn_predict = cross_val_predict(knn_model, x_std[knn_variable_list], y, cv=5)
        print(confusion_matrix(y_true=y, y_pred=knn_predict))
        conf_matr = confusion_matrix(y_true=y, y_pred=knn_predict)
        model_search_knn.append([grid_search.best_params_, grid_search.best_score_, conf_matr[0][0],
                                 conf_matr[0][1], conf_matr[1][0], conf_matr[1][1], list(x_std[knn_variable_list])])
        # else:
        #     print(knn_variable_list)
        #     grid_search.fit(x_std[knn_variable_list], y)
        #     print(f'Best parameters for current grid seach: {grid_search.best_params_}')
        #     print(f'Best score for current grid seach: {grid_search.best_score_}')
        #     # Define parameters of k-nearest neighbors from grid search
        #     knn_model = KNeighborsClassifier(metric='minkowski', n_neighbors=grid_search.best_params_['n_neighbors'],
        #                     weights=grid_search.best_params_['weights'])
        #     # Cross-validate and predict using Support-vector machine classifer
        #     knn_predict = cross_val_predict(knn_model, x_std[knn_variable_list], y, cv=5)
        #     print(confusion_matrix(y_true=y, y_pred=knn_predict))
        #     conf_matr = confusion_matrix(y_true=y, y_pred=knn_predict)
        #     model_search_knn.append([grid_search.best_params_, grid_search.best_score_, conf_matr[0][0],
        #                              conf_matr[0][1], conf_matr[1][0], conf_matr[1][1], list(x_std[knn_variable_list])])
# Create DataFrame of k-nearest neighbors results
model_search_knn = pd.DataFrame(model_search_knn, columns=['best_model_params_grid_search', 'best_score_grid_search',
                                             'true_negatives', 'false_positives',
                                             'false_negatives', 'true_positives', 'variables_used'])
# Create recall, precision, f1-score columns
model_search_knn['recall'] = model_search_knn.true_positives/(model_search_knn.true_positives + model_search_knn.false_negatives)
model_search_knn['precision'] = model_search_knn.true_positives/(model_search_knn.true_positives + model_search_knn.false_positives)
model_search_knn['f1_score'] = 2 * (model_search_knn.precision * model_search_knn.recall) / (model_search_knn.precision + model_search_knn.recall)
# Sort DataFrame
model_search_knn = model_search_knn.sort_values(by=['f1_score'], ascending=False)
print(model_search_knn)

if len(model_search_knn.loc[model_search_knn.f1_score==model_search_knn.f1_score.max()]) > 1:
    print("Fix multiple best model problem for rfc")
else:
    top_model_result_knn = model_search_knn.loc[model_search_knn.f1_score==model_search_knn.f1_score.max()]










grid_search.fit(x_std[['exang_0', 'exang_1']], y)
print(grid_search.best_params_, grid_search.best_score_)

knn_model = KNeighborsClassifier(metric='minkowski', n_neighbors=33, weights='uniform')
knn_predict = cross_val_predict(knn_model, x_std, y, cv=5)
print(confusion_matrix(y_true=y, y_pred=knn_predict))

### Gradient-boosting model
# Create copy of hungarian for non-regression modeling
model = hungarian.copy()
# Drop columns
model = model.drop(columns=['id', 'chol', 'thalrest', 'trestbps', 'ekgyr', 'ekgmo', 'ekgday', 'cyr', 'cmo', 'cday',
                            'ekg_date', 'cardiac_cath_date', 'rldv5', 'lvx3', 'lvx4', 'lvf', 'pro', 'proto',
                            'rldv5_rldv5e_pca'])
# Dummy variable categorical variables
model = pd.get_dummies(data=model, columns=categorical_variables[:-7] + [categorical_variables[-6]] + [categorical_variables[-4]], drop_first=False)
# Create target variable
y = model['num']
# Create feature variables
x = model.drop(columns='num')

# Obtain list of all feature variables
x_all = list(x)
model_search_gbm = []

while True:
    print(x.shape)
    print('------')
    print("\n")
    # Baseline model
    gbm_baseline = GradientBoostingClassifier()
    # Cross-validate
    cross_val_score_gbm = cross_val_score(gbm_baseline, x, y, cv=cv)
    # Baseline cv score mean
    # print(f"Baseline gbm cross_val_score mean: {cross_val_score_gbm.mean()}")

    # Begin parameter tuning for GBM
    # Set initial values (will be tuned later)
    min_samples_split = 3
    min_samples_leaf = 20
    max_depth = 5
    max_features = 'sqrt'
    subsample = 0.8
    learning_rate = 0.1
    # Set param_grid to tune n_estimators
    param_grid = {'n_estimators': np.arange(20,81,10)}

    # Tune n_estimators
    gbm_one = GradientBoostingClassifier(learning_rate= learning_rate, min_samples_split= min_samples_split,
                                         min_samples_leaf= min_samples_leaf, max_depth= max_depth,
                                         max_features= max_features, subsample= subsample)
    grid_search = GridSearchCV(gbm_one, param_grid, cv=cv) # , scoring='recall'
    grid_search.fit(x, y)
    # print(grid_search.best_params_, grid_search.best_score_)
    # Obain n_estimators from grid search
    n_estimators_best_param_grid_search_one = grid_search.best_params_['n_estimators']

    # Tune tree-specific parameters
    param_grid2 = {'max_depth': np.arange(3,20,2), 'min_samples_split': np.arange(10,200,10)}
    # Tune max_depth and min_samples_split
    gbm_two = GradientBoostingClassifier(learning_rate= learning_rate, max_features= max_features,
                                         subsample= subsample, n_estimators=n_estimators_best_param_grid_search_one)
    grid_search = GridSearchCV(gbm_two, param_grid2, cv=cv) # , scoring='recall'
    grid_search.fit(x, y)
    # print(grid_search.best_params_, grid_search.best_score_)
    # Obain max_depth and min_samples_split from grid search
    max_depth_best_param_grid_search_two = grid_search.best_params_['max_depth']
    min_samples_split_best_param_grid_search_two = grid_search.best_params_['min_samples_split']

    # Tune min_samples_leaf
    param_grid3 = {'min_samples_leaf': np.arange(1,15,1)}
    gbm_three = GradientBoostingClassifier(learning_rate= learning_rate, max_features= max_features,
                                         subsample= subsample, n_estimators=n_estimators_best_param_grid_search_one,
                                           max_depth= max_depth_best_param_grid_search_two,
                                           min_samples_split= min_samples_split_best_param_grid_search_two)
    grid_search = GridSearchCV(gbm_three, param_grid3, cv=cv) # , scoring='recall'
    grid_search.fit(x, y)
    # print(grid_search.best_params_, grid_search.best_score_)
    # Obain min_samples_leaf from grid search
    min_samples_leaf_best_param_grid_search_three = grid_search.best_params_['min_samples_leaf']

    # Tune max_features
    param_grid4 = {'max_features': np.arange(2,20,1)}
    gbm_four = GradientBoostingClassifier(learning_rate= learning_rate, subsample= subsample,
                                          n_estimators=n_estimators_best_param_grid_search_one,
                                          max_depth= max_depth_best_param_grid_search_two,
                                          min_samples_split= min_samples_split_best_param_grid_search_two,
                                          min_samples_leaf= min_samples_leaf_best_param_grid_search_three)
    grid_search = GridSearchCV(gbm_four, param_grid4, cv=cv) # , scoring='recall'
    grid_search.fit(x, y)
    # print(grid_search.best_params_, grid_search.best_score_)
    # Obain max_features from grid search
    max_features_best_param_grid_search_four = grid_search.best_params_['max_features']

    # Tune subsample
    param_grid5 = {'subsample': np.arange(0.6,1,0.05)}
    gbm_five = GradientBoostingClassifier(learning_rate= learning_rate,
                                          n_estimators=n_estimators_best_param_grid_search_one,
                                          max_depth=max_depth_best_param_grid_search_two,
                                          min_samples_split=min_samples_split_best_param_grid_search_two,
                                          min_samples_leaf=min_samples_leaf_best_param_grid_search_three,
                                          max_features=max_features_best_param_grid_search_four)
    grid_search = GridSearchCV(gbm_five, param_grid5, cv=cv) # , scoring='recall'
    grid_search.fit(x, y)
    # print(grid_search.best_params_, grid_search.best_score_)
    # Obtain subsample from grid search
    subsample_best_param_grid_search_five = grid_search.best_params_['subsample']

    # Tune learning rate and increase n_estimators proportionally
    param_grid_list = [[learning_rate, n_estimators_best_param_grid_search_one],
                       [learning_rate/2, n_estimators_best_param_grid_search_one*2],
                       [learning_rate/5, n_estimators_best_param_grid_search_one*5],
                       [learning_rate/10, n_estimators_best_param_grid_search_one*10],
                       [learning_rate/20, n_estimators_best_param_grid_search_one*20],
                       [learning_rate/30, n_estimators_best_param_grid_search_one*30],
                       [learning_rate/40, n_estimators_best_param_grid_search_one*40],
                       [learning_rate/50, n_estimators_best_param_grid_search_one*50]]
    # Append l_rate, n_ests, and cross_val_score mean
    cross_val_score_gbm_six_means = []
    for l_rate, n_ests in param_grid_list:
        # print(l_rate, n_ests)
        gbm_six = GradientBoostingClassifier(learning_rate=l_rate, n_estimators=n_ests,
                                             max_depth=max_depth_best_param_grid_search_two,
                                             min_samples_split=min_samples_split_best_param_grid_search_two,
                                             min_samples_leaf=min_samples_leaf_best_param_grid_search_three,
                                             max_features=max_features_best_param_grid_search_four,
                                             subsample=subsample_best_param_grid_search_five)
        cross_val_score_gbm_six = cross_val_score(gbm_six, x, y, cv=cv)
        # print(cross_val_score_gbm_six)
        # print(cross_val_score_gbm_six.mean())
        cross_val_score_gbm_six_means.append([l_rate, n_ests, cross_val_score_gbm_six.mean()])
        # Retrieve best values for learning_rate and n_estimators based on max value of cross_val_score_gbm_six.mean()
        learning_rate_n_estimators_best_param_grid_list = list(filter(lambda x: x[2] == max(map(lambda x: x[2],
                                                            cross_val_score_gbm_six_means)), cross_val_score_gbm_six_means))[0]

    gbm_final = GradientBoostingClassifier(learning_rate=learning_rate_n_estimators_best_param_grid_list[0],
                                           n_estimators=learning_rate_n_estimators_best_param_grid_list[1],
                                           max_depth=max_depth_best_param_grid_search_two,
                                           min_samples_split=min_samples_split_best_param_grid_search_two,
                                           min_samples_leaf=min_samples_leaf_best_param_grid_search_three,
                                           max_features=max_features_best_param_grid_search_four,
                                           subsample=subsample_best_param_grid_search_five)
    gbm_predict = cross_val_predict(gbm_final, x, y, cv=5)
    conf_matr = confusion_matrix(y_true=y, y_pred=gbm_predict)
    # print(conf_matr)
    model_search_gbm.append([gbm_final.get_params(), conf_matr[0][0], conf_matr[0][1],
                             conf_matr[1][0], conf_matr[1][1], set(x_all).difference(x)])
    # Obtain feature importances
    gradient_boosting_feature_importance = pd.DataFrame(data=[list(x),
        gbm_final.fit(x, y).feature_importances_.tolist()]).T.rename(columns={0:'variable',
        1:'importance'}).sort_values(by='importance', ascending=False)
    # Remove 'worst' variables one-by-one
    print(gradient_boosting_feature_importance.loc[gradient_boosting_feature_importance.importance < 0.10])
    if len(gradient_boosting_feature_importance.loc[gradient_boosting_feature_importance.importance < 0.01]) > 0:
        for i in range(1, len(gradient_boosting_feature_importance.loc[gradient_boosting_feature_importance.importance < 0.01]) + 1):
            print(f"'Worst' variable being examined: "
                  f"{gradient_boosting_feature_importance.loc[gradient_boosting_feature_importance.importance < 0.01].variable.values[-i]}")
            bottom_variable = gradient_boosting_feature_importance.loc[gradient_boosting_feature_importance.importance < 0.01].variable.values[-i]
            # If True, means it is a categorical variable - want to check for other one-hot encoded variables
            # if any(x in bottom_variable for x in sorted([x for x in list(set([x.split('_')[-1] for x in list(x)])) if len(x) == 1])):
            bottom_variable = bottom_variable.split('_')[0]
            bottom_variable = [col for col in list(x) if bottom_variable in col]
            compare_counter = 0
            for var in bottom_variable:
                if var in gradient_boosting_feature_importance.loc[gradient_boosting_feature_importance.importance<0.01].variable.values:
                    compare_counter += 1
            if len(bottom_variable) == compare_counter:
                print(f"Following variable(s) will be dropped from x {bottom_variable}")
                x = x.drop(columns=bottom_variable)
                break
            else:
                print("Next 'worst' variable will be examined for dropping.")
                continue
        # else:
        #     x = x.drop(columns=bottom_variable)
        else:
            break
# Create DataFrame of random forest classifer results
model_search_gbm = pd.DataFrame(model_search_gbm, columns=['model_params_grid_search',
                                             'true_negatives', 'false_positives',
                                             'false_negatives', 'true_positives', 'variables_not_used'])
# Create recall and precision columns
model_search_gbm['recall'] = model_search_gbm.true_positives/(model_search_gbm.true_positives + model_search_gbm.false_negatives)
model_search_gbm['precision'] = model_search_gbm.true_positives/(model_search_gbm.true_positives + model_search_gbm.false_positives)
model_search_gbm['f1_score'] = 2 * (model_search_gbm.precision * model_search_gbm.recall) / (model_search_gbm.precision + model_search_gbm.recall)
# Sort DataFrame
model_search_gbm = model_search_gbm.sort_values(by=['f1_score'], ascending=False)

# Choose top model from gbm model search
if len(model_search_gbm.loc[model_search_gbm.f1_score==model_search_gbm.f1_score.max()]) > 1:
    top_model_result_gbm = model_search_gbm.loc[(model_search_gbm.f1_score == model_search_gbm.f1_score.max()) &
        (model_search_gbm['variables_not_used'].apply(len) == max(map(lambda x: len(x[list(model_search_gbm).index('variables_not_used')]),
         model_search_gbm.loc[model_search_gbm.f1_score==model_search_gbm.f1_score.max()].values)))]
















## Sex
# Get counts of sex
print(hungarian.sex.value_counts())
print(f'The hungarian dataset consists of {hungarian.sex.value_counts()[0]} females and'
      f' {hungarian.sex.value_counts()[1]} males.')

# Bar graph of sex by num
plt.figure()
sex_dict = {0: "female", 1: "male"}
sns.countplot(x="sex", hue="num", data=hungarian).set(title='Heart Disease Indicator by Sex', xticklabels=sex_dict.values())
plt.show()

# Crosstab of sex by num
print(pd.crosstab(index=hungarian.sex, columns=hungarian.num))

# Crosstab of sex by num - all values normalized
# Of all patients in dataset, 32% were males that had heart disease. 4% were females that had heart disease.
print(pd.crosstab(index=hungarian.sex, columns=hungarian.num, normalize='all'))

# Crosstab of sex by num - rows normalized
# 15% of females had heart disease. 44% of males had heart disease.
print(pd.crosstab(index=hungarian.sex, columns=hungarian.num, normalize='index'))

# Crosstab of sex by num - columns normalized
# 89% of the patients with heart disease were males. 11% were females.
print(pd.crosstab(index=hungarian.sex, columns=hungarian.num, normalize='columns'))

# Contingency table of sex by num
contingency = pd.crosstab(index=hungarian.sex, columns=hungarian.num)
print(contingency)



if p <= strong_alpha_value:
    print(f"Reject the null hypothesis of no association between {contingency.index.name} and diagnosis of heart "
          f"disease and conclude there is an association between {contingency.index.name} and diagnosis of heart "
          f"disease. The probability of a heart disease diagnosis is not the same for male and female patients.")
else:
    print(f"Fail to reject the null of no association between sex and diagnosis of heart disease. The probability of a "
          f"heart disease diagnosis is the same regardless of a patient's sex.")

# Compute odds ratio and risk ratio
table = sm.stats.Table2x2(contingency)
print(table.summary())
print(f"The odds ratio is {table.oddsratio}. This means males are {round(table.oddsratio,2)} times more likely to be "
      f"diagnosed with heart disease than females.")

## Painloc
# Bar graph of painloc by num
plt.figure()
painloc_dict = {0: "otherwise", 1: "substernal"}
sns.countplot(x="painloc", hue="num", data=hungarian).set(title='Heart Disease Indicator by Pain Location', xticklabels=painloc_dict.values())
plt.show()

# Contingency table of painloc by num
contingency = pd.crosstab(index=hungarian.painloc, columns=hungarian.num)
print(contingency)
# Pearson chi-square test
chi, p, dof, expected = stats.chi2_contingency(contingency)
print(f"The chi-square value for {contingency.index.name} and {contingency.columns.name} is {chi}, and the p-value is"
      f" {p}, respectfully.")
if p <= strong_alpha_value:
    print(f"Reject the null hypothesis of no association between {contingency.index.name} and diagnosis of heart "
          f"disease and conclude there is an association between {contingency.index.name} and diagnosis of heart "
          f"disease. The probability of a heart disease diagnosis is not the same based on chest pain location.")
else:
    print(f"Fail to reject the null of no association between {contingency.index.name} and diagnosis of heart disease. "
          f"The probability of a heart disease diagnosis is the same regardless of chest pain location.")

# Fisher's Exact chi-square



# Compute odds ratio and risk ratio
table = sm.stats.Table2x2(contingency)
print(table.summary())
print(f"The odds ratio is {table.oddsratio}.")

## Painexer
# Bar graph of painexer by num
plt.figure()
painexer_dict = {0: "otherwise", 1: "provoked by exertion"}
sns.countplot(x="painexer", hue="num", data=hungarian).set(title='Heart Disease Indicator by Pain Exertion', xticklabels=painexer_dict.values())
plt.show()

# Contingency table of painexer by num
contingency = pd.crosstab(index=hungarian.painexer, columns=hungarian.num)
print(contingency)
# Pearson chi-square test
chi, p, dof, expected = stats.chi2_contingency(contingency)
print(f"The chi-square value for {contingency.index.name} and {contingency.columns.name} is {chi}, and the p-value is"
      f" {p}, respectfully. The expected values are\n{expected}.")
if p <= strong_alpha_value:
    print(f"Reject the null hypothesis of no association between {contingency.index.name} and diagnosis of heart "
          f"disease and conclude there is an association between {contingency.index.name} and diagnosis of heart "
          f"disease. The probability of a heart disease diagnosis is not the same based on how chest pain is provoked.")
else:
    print(f"Fail to reject the null of no association between {contingency.index.name} and diagnosis of heart disease. "
          f"The probability of a heart disease diagnosis is the same regardless of how chest pain is provoked.")

# Compute odds ratio and risk ratio
table = sm.stats.Table2x2(contingency)
print(table.summary())
print(f"The odds ratio is {table.oddsratio}. This means patients with their chest pain provoked by exertion are "
      f"{round(table.oddsratio,2)} times more likely to have a diagnosis of heart disease than those patients with "
      f"their chest pain provoked otherwise.")


## Relrest
# Bar graph of relrest by num
plt.figure()
relrest_dict = {0: "otherwise", 1: "relieved after rest"}
sns.countplot(x="relrest", hue="num", data=hungarian).set(title='Heart Disease Indicator by Pain Relief', xticklabels=relrest_dict.values())
plt.show()

# Contingency table of relrest by num
contingency = pd.crosstab(index=hungarian.relrest, columns=hungarian.num)
print(contingency)
# Pearson chi-square test
chi, p, dof, expected = stats.chi2_contingency(contingency)
print(f"The chi-square value for {contingency.index.name} and {contingency.columns.name} is {chi}, and the p-value is"
      f" {p}, respectfully. The expected values are\n{expected}.")
if p <= strong_alpha_value:
    print(f"Reject the null hypothesis of no association between {contingency.index.name} and diagnosis of heart "
          f"disease and conclude there is an association between {contingency.index.name} and diagnosis of heart "
          f"disease. The probability of a heart disease diagnosis is not the same for pain relieved after rest and "
          f"otherwise.")
else:
    print(f"Fail to reject the null of no association between {contingency.index.name} and diagnosis of heart disease. "
          f"The probability of a heart disease diagnosis is the same regardless of when the pain is relieved.")

# Compute odds ratio and risk ratio
table = sm.stats.Table2x2(contingency)
print(table.summary())
print(f"The odds ratio is {table.oddsratio}. This means patients with their chest pain relieved after rest are "
      f"{round(table.oddsratio,2)} times more likely to have a diagnosis of heart disease than those patients with "
      f"their chest pain relieved otherwise.")

## Cp
# Bar graph of cp by num
plt.figure()
cp_dict = {1: "typical angina", 2: "atypical angina", 3: "non-anginal pain", 4: "asymptomatic"}
sns.countplot(x="cp", hue="num", data=hungarian).set(title='Heart Disease Indicator by Chest Pain Type', xticklabels=cp_dict.values())
plt.show()

# Contingency table of cp by cum
contingency = pd.crosstab(index=hungarian.cp, columns=hungarian.num)
print(contingency)
# Pearson chi-square test
chi, p, dof, expected = stats.chi2_contingency(contingency)
print(f"The chi-square value for {contingency.index.name} and {contingency.columns.name} is {chi}, and the p-value is"
      f" {p}, respectfully.")
if p <= strong_alpha_value:
    print(f"Reject the null hypothesis of no association between {contingency.index.name} and diagnosis of heart "
          f"disease and conclude there is an association between {contingency.index.name} and diagnosis of heart "
          f"disease. The probability of a heart disease diagnosis is not the same depending on chest pain type.")
else:
    print(
        f"Fail to reject the null of no association between {contingency.index.name} and diagnosis of heart disease. "
        f"The probability of a heart disease diagnosis is the same regardless of chest pain type.")

# Fisher's Exact chi-square

# Compute odds ratio and risk ratio
### Figure out local odds ratios
table = sm.stats.Table(contingency)
print(table.local_oddsratios)





























# Distribution plot of age of all patients
plt.figure(), sns.distplot(hungarian['age'], kde=True, fit=stats.norm, rug=True).set_title("Age Distribution of Patients")
plt.show()

# Statistical undersatanding of age of all patients
print(f"Mean +/- std of {hungarian['age'].name}: {round(hungarian['age'].describe()['mean'],2)} +/"
      f" {round(hungarian['age'].describe()['std'],2)}. This means 68% of my patients lie between the ages of"
      f" {round(hungarian['age'].describe()['mean'] - hungarian['age'].describe()['std'],2)} and"
      f" {round(hungarian['age'].describe()['mean'] + hungarian['age'].describe()['std'],2)}.")
standard_devations = 2
print(f"Mean +/- {standard_devations} std of {hungarian['age'].name}: {round(hungarian['age'].describe()['mean'],2)} +/"
      f" {round(hungarian['age'].describe()['std'] * standard_devations,2)}. This means 95% of my patients lie between the ages of"
      f" {round(hungarian['age'].describe()['mean'] - (standard_devations * hungarian['age'].describe()['std']),2)} and"
      f" {round(hungarian['age'].describe()['mean'] + (standard_devations * hungarian['age'].describe()['std']),2)}.")
standard_devations = 3
print(f"Mean +/- {standard_devations} std of {hungarian['age'].name}: {round(hungarian['age'].describe()['mean'],2)} +/"
      f" {round(hungarian['age'].describe()['std'] * standard_devations,2)}. This means 99.7% of my patients lie between the ages of"
      f" {round(hungarian['age'].describe()['mean'] - (standard_devations * hungarian['age'].describe()['std']),2)} and"
      f" {round(hungarian['age'].describe()['mean'] + (standard_devations * hungarian['age'].describe()['std']),2)}.")
print(f"Mode of {hungarian['age'].name}: {hungarian['age'].mode()[0]}\nMedian of {hungarian['age'].name}: {hungarian['age'].median()}")

# Distribution plot of age of patients broken down by sex - female
plt.figure(), sns.distplot(hungarian.loc[hungarian['sex']==0, 'age'], label='Female Age Distribution',kde=True, fit=stats.norm)
plt.legend()
plt.show()

# Distribution plot of age of patients broken down by sex - male
plt.figure(), sns.distplot(hungarian.loc[hungarian['sex']==1, 'age'], label='Male Age Distribution',kde=True, fit=stats.norm)
plt.legend()
plt.show()

# Women age information
print(f"Mean +/- std of {hungarian.loc[hungarian['sex']==0, 'age'].name} for women: "
      f"{round(hungarian.loc[hungarian['sex']==0, 'age'].describe()['mean'],2)} +/ "
      f"{round(hungarian.loc[hungarian['sex']==0, 'age'].describe()['std'],2)}")

print(f"Mode of {hungarian.loc[hungarian['sex']==0, 'age'].name} for women: "
      f"{hungarian.loc[hungarian['sex']==0, 'age'].mode()[0]}\nMedian of "
      f"{hungarian.loc[hungarian['sex']==0, 'age'].name} for women: + "
      f"{hungarian.loc[hungarian['sex']==0, 'age'].median()}")
print('\n')
# Men age information
print(f"Mean +/- std of {hungarian.loc[hungarian['sex']==1, 'age'].name} for men: "
      f"{round(hungarian.loc[hungarian['sex']==1, 'age'].describe()['mean'],2)} +/ "
      f"{round(hungarian.loc[hungarian['sex']==1, 'age'].describe()['std'],2)}")

print(f"Mode of {hungarian.loc[hungarian['sex']==1, 'age'].name} for men: "
      f"{hungarian.loc[hungarian['sex']==1, 'age'].mode()[0]}\nMedian of "
      f"{hungarian.loc[hungarian['sex']==1, 'age'].name} for men: + "
      f"{hungarian.loc[hungarian['sex']==1, 'age'].median()}")


sns.scatterplot(x='age', y='num', data=hungarian)
pd.crosstab(index=hungarian.age,columns=hungarian.num)