"""
=============================================
Compare ensemble classifiers using resampling
=============================================

Ensemble classifiers have shown to improve classification performance compare
to single learner. However, they will be affected by class imbalance. This
example shows the benefit of balancing the training set before to learn
learners. We are making the comparison with non-balanced ensemble methods.

We make a comparison using the balanced accuracy and geometric mean which are
metrics widely used in the literature to evaluate models learned on imbalanced
set.
"""

# Authors: Guillaume Lemaitre <g.lemaitre58@gmail.com>
# License: MIT

# %%
print(__doc__)

# %% [markdown]
# Load an imbalanced dataset
# --------------------------
#
# We will load the UCI SatImage dataset which has an imbalanced ratio of 9.3:1
# (number of majority sample for a minority sample). The data are then split
# into training and testing.

# %%
from sklearn.model_selection import train_test_split
import pandas as pd
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest
from sklearn.preprocessing import StandardScaler, scale
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV
from sklearn.utils import compute_class_weight

data = pd.read_csv('./data/wanzhou_island.csv')
target = 'value'
IDCol = 'ID'
GeoID = data[IDCol]
print(data[target].value_counts())
#     x_columns = [x for x in data.columns if x not in [target,IDCol,'GRID_CODE']]
x_columns = ['Elevation', 'Slope', 'Aspect', 'TRI', 'Curvature', 'Lithology', 'River', 'NDVI', 'NDWI', 'Rainfall', 'Earthquake', 'Land_use']

X = data[x_columns]
y = data[target]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4,stratify=y, random_state=0)

# %% 
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.compose import make_column_selector as selector
from imblearn.ensemble import BalancedRandomForestClassifier

stdscaler = StandardScaler()
pca = PCA(n_components='mle')

num_pipe = make_pipeline(
    stdscaler, 
    SimpleImputer(strategy="mean", add_indicator=True), 
    pca
)
cat_pipe = make_pipeline(
    SimpleImputer(strategy="constant", fill_value="missing"),
    OneHotEncoder(handle_unknown="ignore"),
)

preprocessor_tree = make_column_transformer(
    (num_pipe, selector(dtype_include="number")),
    (cat_pipe, selector(dtype_include="category")),
    n_jobs=2,
)

rf_clf = make_pipeline(
    preprocessor_tree, RandomForestClassifier(random_state=42, n_jobs=-1)
)

weighted_rf_clf = make_pipeline(
    preprocessor_tree, RandomForestClassifier(random_state=42, n_jobs=-1, class_weight='balanced')
)

balanced_rf_clf = BalancedRandomForestClassifier(random_state=42, n_jobs=-1)

rf_clf.fit(X_train, y_train)
y_pred_rf_clf = rf_clf.predict(X_test)
y_prob_rf_clf = rf_clf.predict_proba(X_test)

weighted_rf_clf.fit(X_train, y_train)
y_pred_weighted_rf_clf = weighted_rf_clf.predict(X_test)
y_prob_weighted_rf_clf = weighted_rf_clf.predict_proba(X_test)

balanced_rf_clf.fit(X_train, y_train)
y_pred_balanced_rf_clf = balanced_rf_clf.predict(X_test)
y_prob_balanced_rf_clf = balanced_rf_clf.predict_proba(X_test)

import matplotlib.pyplot as plt
from sklearn.metrics import RocCurveDisplay

fig, ax = plt.subplots()

models = [
    ("RF", rf_clf),
    ("Weighted RF", weighted_rf_clf),
    ("Balanced RF", balanced_rf_clf),
]

model_displays = {}
for name, pipeline in models:
    model_displays[name] = RocCurveDisplay.from_estimator(
        pipeline, X_test, y_test, ax=ax, name=name
    )
_ = ax.set_title("ROC curve")
plt.show()
# %% [markdown]
# Classification using a single decision tree
# -------------------------------------------
#
# We train a decision tree classifier which will be used as a baseline for the
# rest of this example.
#
# The results are reported in terms of balanced accuracy and geometric mean
# which are metrics widely used in the literature to validate model trained on
# imbalanced set.

# %%
from sklearn.tree import DecisionTreeClassifier

tree = DecisionTreeClassifier()
tree.fit(X_train, y_train)
y_pred_tree = tree.predict(X_test)

# %%
from sklearn.metrics import balanced_accuracy_score
from imblearn.metrics import geometric_mean_score

print("Decision tree classifier performance:")
print(
    f"Balanced accuracy: {balanced_accuracy_score(y_test, y_pred_tree):.2f} - "
    f"Geometric mean {geometric_mean_score(y_test, y_pred_tree):.2f}"
)

# %%
import seaborn as sns
from sklearn.metrics import plot_confusion_matrix

sns.set_context("poster")

disp = plot_confusion_matrix(tree, X_test, y_test, colorbar=False)
_ = disp.ax_.set_title("Decision tree")

# %% [markdown]
# Classification using bagging classifier with and without sampling
# -----------------------------------------------------------------
#
# Instead of using a single tree, we will check if an ensemble of decsion tree
# can actually alleviate the issue induced by the class imbalancing. First, we
# will use a bagging classifier and its counter part which internally uses a
# random under-sampling to balanced each boostrap sample.

# %%
from sklearn.ensemble import BaggingClassifier, RandomForestClassifier
from imblearn.ensemble import BalancedBaggingClassifier

bagging = BaggingClassifier(n_estimators=50, random_state=0)
balanced_bagging = BalancedBaggingClassifier(n_estimators=50, random_state=0)

bagging.fit(X_train, y_train)
balanced_bagging.fit(X_train, y_train)

y_pred_bc = bagging.predict(X_test)
y_pred_bbc = balanced_bagging.predict(X_test)

# %% [markdown]
# Balancing each bootstrap sample allows to increase significantly the balanced
# accuracy and the geometric mean.

# %%
print("Bagging classifier performance:")
print(
    f"Balanced accuracy: {balanced_accuracy_score(y_test, y_pred_bc):.2f} - "
    f"Geometric mean {geometric_mean_score(y_test, y_pred_bc):.2f}"
)
print("Balanced Bagging classifier performance:")
print(
    f"Balanced accuracy: {balanced_accuracy_score(y_test, y_pred_bbc):.2f} - "
    f"Geometric mean {geometric_mean_score(y_test, y_pred_bbc):.2f}"
)

# %%
import matplotlib.pyplot as plt

fig, axs = plt.subplots(ncols=2, figsize=(10, 5))
plot_confusion_matrix(bagging, X_test, y_test, ax=axs[0], colorbar=False)
axs[0].set_title("Bagging")

plot_confusion_matrix(balanced_bagging, X_test, y_test, ax=axs[1], colorbar=False)
axs[1].set_title("Balanced Bagging")

fig.tight_layout()

# %% [markdown]
# Classification using random forest classifier with and without sampling
# -----------------------------------------------------------------------
#
# Random forest is another popular ensemble method and it is usually
# outperforming bagging. Here, we used a vanilla random forest and its balanced
# counterpart in which each bootstrap sample is balanced.

# %%
from sklearn.ensemble import RandomForestClassifier
from imblearn.ensemble import BalancedRandomForestClassifier

rf = RandomForestClassifier(n_estimators=50, random_state=0)
brf = BalancedRandomForestClassifier(n_estimators=50, random_state=0)

rf.fit(X_train, y_train)
brf.fit(X_train, y_train)

y_pred_rf = rf.predict(X_test)
y_pred_brf = brf.predict(X_test)

# %% [markdown]
# Similarly to the previous experiment, the balanced classifier outperform the
# classifier which learn from imbalanced bootstrap samples. In addition, random
# forest outsperforms the bagging classifier.

# %%
print("Random Forest classifier performance:")
print(
    f"Balanced accuracy: {balanced_accuracy_score(y_test, y_pred_rf):.2f} - "
    f"Geometric mean {geometric_mean_score(y_test, y_pred_rf):.2f}"
)
print("Balanced Random Forest classifier performance:")
print(
    f"Balanced accuracy: {balanced_accuracy_score(y_test, y_pred_brf):.2f} - "
    f"Geometric mean {geometric_mean_score(y_test, y_pred_brf):.2f}"
)

# %%
fig, axs = plt.subplots(ncols=2, figsize=(10, 5))
plot_confusion_matrix(rf, X_test, y_test, ax=axs[0], colorbar=False)
axs[0].set_title("Random forest")

plot_confusion_matrix(brf, X_test, y_test, ax=axs[1], colorbar=False)
axs[1].set_title("Balanced random forest")

fig.tight_layout()

# %% [markdown]
# Boosting classifier
# -------------------
#
# In the same manner, easy ensemble classifier is a bag of balanced AdaBoost
# classifier. However, it will be slower to train than random forest and will
# achieve worse performance.

# %%
from sklearn.ensemble import AdaBoostClassifier
from imblearn.ensemble import EasyEnsembleClassifier, RUSBoostClassifier

base_estimator = AdaBoostClassifier(n_estimators=10)
eec = EasyEnsembleClassifier(n_estimators=10, base_estimator=base_estimator)
eec.fit(X_train, y_train)
y_pred_eec = eec.predict(X_test)

rusboost = RUSBoostClassifier(n_estimators=10, base_estimator=base_estimator)
rusboost.fit(X_train, y_train)
y_pred_rusboost = rusboost.predict(X_test)

# %%
print("Easy ensemble classifier performance:")
print(
    f"Balanced accuracy: {balanced_accuracy_score(y_test, y_pred_eec):.2f} - "
    f"Geometric mean {geometric_mean_score(y_test, y_pred_eec):.2f}"
)
print("RUSBoost classifier performance:")
print(
    f"Balanced accuracy: {balanced_accuracy_score(y_test, y_pred_rusboost):.2f} - "
    f"Geometric mean {geometric_mean_score(y_test, y_pred_rusboost):.2f}"
)

# %%
fig, axs = plt.subplots(ncols=2, figsize=(10, 5))

plot_confusion_matrix(eec, X_test, y_test, ax=axs[0], colorbar=False)
axs[0].set_title("Easy Ensemble")
plot_confusion_matrix(rusboost, X_test, y_test, ax=axs[1], colorbar=False)
axs[1].set_title("RUSBoost classifier")

fig.tight_layout()
plt.show()
