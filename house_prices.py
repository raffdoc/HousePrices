# Predict the SalePrice
__author__ = 'mizio'
# import csv as csv
import numpy as np
import pandas as pd
# import matplotlib
# matplotlib.use('TkAgg')
import pylab as plt
from fancyimpute import MICE
# import sys
# sys.path.append('/custom/path/to/modules')
import random
# from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import OneHotEncoder
from scipy.stats import skew
from sklearn.model_selection import cross_val_score
# import math

class HousePrices(object):
    def __init__(self):
        self.df = HousePrices.df
        self.df_test = HousePrices.df_test
        self.df_all_feature_var_names = []


    ''' Pandas Data Frame '''
    df = pd.read_csv('/home/user/Documents/Kaggle/HousePrices/train.csv', header=0)
    df_test = pd.read_csv('/home/user/Documents/Kaggle/HousePrices/test.csv', header=0)

    def square_feet_to_meters(self, area):
        square_meter_per_square_feet = 0.3048**2
        return area*square_meter_per_square_feet

    def extract_numerical_features(self, df):
        df = df.copy()
        return df.select_dtypes(include=[np.number])

    def extract_non_numerical_features(self, df):
        df = df.copy()
        return df.select_dtypes(exclude=[np.number])


    def clean_data(self, df):
        df = df.copy()
        # Imputation using MICE
        numerical_features_names = self.extract_numerical_features(df)._get_axis(1)
        df[numerical_features_names] = self.estimate_by_mice(df[numerical_features_names])
        return df

    def encode_labels_in_numeric_format(self, df, estimated_var):
        # Transform non-numeric labels into numerical values
        # Cons.: gives additional unwanted structure to data, since some values are high and others low, despite labels where no such comparing measure exists.
        # Alternative: use one-hot-encoding giving all labels their own column represented with only binary values.
        le = LabelEncoder()
        le.fit(df[estimated_var].values)
        # Check that all values are represented
        list(le.classes_)
        df[''.join([estimated_var, 'Num'])] = le.transform(df[estimated_var].values)

    def label_classes(self, df, estimated_var):
        le = LabelEncoder()
        le.fit(df[estimated_var].values)
        return le.classes_


    def one_hot_encoder(self, df, estimated_var):
        ohe = OneHotEncoder()
        # Get every feature_var_name and exclude nan in label_classes
        label_classes = self.label_classes(df, estimated_var)
        label_classes = np.asarray(map(lambda x: str(x), label_classes))
        # if (estimated_var == 'SaleType') & (not any(df.columns == 'SalePrice')):
        #     print 'hello'
        # if any(label_classes == 'nan'):
        #     print 'debug'
        label_classes_is_not_nan = label_classes != 'nan'
        label_classes = label_classes[label_classes_is_not_nan]
        new_one_hot_encoded_features = map(lambda x: ''.join([estimated_var, '_', str(x)]), label_classes)

        # Create new feature_var columns with one-hot encoded values
        feature_var_values = ohe.fit_transform(np.reshape(np.array(df[''.join([estimated_var, 'Num'])].values), (df.shape[0], 1))).toarray().astype(int)
        column_index = 0
        for ite in new_one_hot_encoded_features:
            df[ite] = feature_var_values[0::, column_index]
            column_index += 1


    def add_feature_var_name_with_zeros(self, df, feature_var_name):
        df[feature_var_name] = np.zeros((df.shape[0], 1), dtype=int)
        pass


    def feature_var_names_in_training_set_not_in_test_set(self, feature_var_names_training, feature_var_names_test):
        feature_var_name_addition_list = []
        for feature_var_name in feature_var_names_training:
            if not any(feature_var_name == feature_var_names_test):
                feature_var_name_addition_list.append(feature_var_name)
        return np.array(feature_var_name_addition_list)


    def feature_mapping_to_numerical_values(self, df):
        is_one_hot_encoder = 1
        if is_one_hot_encoder:
            non_numerical_feature_names = self.extract_non_numerical_features(df)._get_axis(1)
            for feature_name in non_numerical_feature_names:
                self.encode_labels_in_numeric_format(df, feature_name)
                self.one_hot_encoder(df, feature_name)

            # Assume that training set has all possible feature_var_names
            # Although it may occur in real life that a training set may hold a feature_var_name. But it is probably avoided since such features cannot
            # be part of the trained learning algo.
            # Add missing feature_var_names of traning set not occuring in test set. Add these with zeros in columns.
            if not any(df.columns == 'SalePrice'):
                feature_var_names_traning_set = self.df_all_feature_var_names
                feature_var_name_addition_list = self.feature_var_names_in_training_set_not_in_test_set(feature_var_names_traning_set, df.columns)
                for ite in feature_var_name_addition_list:
                    self.add_feature_var_name_with_zeros(df, ite)
        else:
        # is_label_encoder = 1
        # if is_label_encoder:
            non_numerical_feature_names = self.extract_non_numerical_features(df)._get_axis(1)
            for feature_name in non_numerical_feature_names:
                self.encode_labels_in_numeric_format(df, feature_name)
                # if (feature_name == 'MSZoning') or (feature_name == 'SaleCondition'):
                # if (feature_name == 'SaleCondition'):
                #     self.encode_labels_in_numeric_format(df, feature_name)

    def feature_engineering(self, df):
        # df['LotAreaSquareMeters'] = self.square_feet_to_meters(df.LotArea.values)

        # Transform skewed numerics by taking log1p() which is log(feature + 1).
        if any(df.columns == 'SalePrice'):
            df["SalePrice"] = np.log1p(df["SalePrice"])

        # log transform skewed numeric features:
        numeric_feats = df.dtypes[df.dtypes != "object"].index
        skewed_feats = df[numeric_feats].apply(lambda x: skew(x.dropna()))  # compute skewness
        skewed_feats = skewed_feats[skewed_feats > 0.75]
        skewed_feats = skewed_feats.index
        df[skewed_feats] = np.log1p(df[skewed_feats])


    def drop_variable(self, df):
        # Drop all categorical feature columns
        non_numerical_feature_names = self.extract_non_numerical_features(df)._get_axis(1)
        for feature_name in non_numerical_feature_names:
            df = df.drop([''.join([feature_name, 'Num'])], axis=1)
            df = df.drop([feature_name], axis=1)

        df = df.drop(['Id'], axis=1)
        return df


    def prepare_data_random_forest(self, df):
        df = df.copy()
        # self.feature_mapping_to_numerical_values(df)
        self.feature_engineering(df)
        df = self.clean_data(df)
        # df = self.drop_variable(df)
        # df = self.feature_scaling(df)
        return df


    def features_with_null_logical(self, df, axis=1):
        row_length = len(df._get_axis(0))
        # Axis to count non null values in. aggregate_axis=0 implies counting for every feature
        aggregate_axis = 1 - axis
        features_non_null_series = df.count(axis=aggregate_axis)
        # Whenever count() differs from row_length it implies a null value exists in feature column and a False in mask
        mask = row_length == features_non_null_series
        return mask


    def estimate_by_mice(self, df):
        df_estimated_var = df.copy()
        random.seed(129)
        mice = MICE()  #model=RandomForestClassifier(n_estimators=100))
        res = mice.complete(df.values)
        df_estimated_var[df.columns] = res[:][:]
        return df_estimated_var


    def feature_scaling(self, df):
        df = df.copy()
        # Scales all features to be values in [0,1]
        numerical_features_names = self.extract_numerical_features(df)._get_axis(1).values
        df[numerical_features_names] = df[numerical_features_names].apply(lambda x: x/x.max(), axis=0)
        return df

    def missing_values_in_DataFrame(self, df):
        mask = self.features_with_null_logical(df)
        print(df[mask[mask == 0].index.values].isnull().sum())
        print('\n')

    def rmse_cv(self, model, x_train, y_train):
        rmse = np.sqrt(-cross_val_score(model, x_train, y_train, scoring='neg_mean_squared_error', cv=5))
        return (rmse)


def main():
    import xgboost as xgb
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import SGDRegressor
    from sklearn.linear_model import Ridge, RidgeCV, Lasso, LassoCV
    # from sklearn.linear_model import LogisticRegression
    from sklearn.feature_selection import SelectFromModel
    # from sklearn.naive_bayes import GaussianNB
    # from sklearn import svm
    # from collections import OrderedDict
    # from sklearn.ensemble import IsolationForest
    import seaborn as sns
    from sklearn.model_selection import StratifiedKFold
    from sklearn.model_selection import GridSearchCV
    # from sklearn.model_selection import KFold, train_test_split

    ''' Prepare data '''

    house_prices = HousePrices()
    df_publ = house_prices.df.copy()
    df_test_publ = house_prices.df_test.copy()


    df = house_prices.prepare_data_random_forest(df_publ)
    house_prices.df_all_feature_var_names = df[df.columns[df.columns != 'SalePrice']].columns
    print '\n TRAINING DATA:----------------------------------------------- \n'
    print df.head(3)
    print '\n'
    print df.info()
    print '\n'
    print df.describe()

    # Test data
    Id_df_test = house_prices.df_test['Id']  # Submission column
    df_test = house_prices.prepare_data_random_forest(df_test_publ)
    print '\n TEST DATA:----------------------------------------------- \n'
    print df_test.info()
    print '\n'
    print df_test.describe()
    print '\n'

    # Check if feature_var_names of test exist that do not appear in training set
    feature_var_names_addition_to_training_set = house_prices.feature_var_names_in_training_set_not_in_test_set(df_test.columns, df.columns)

    # train_data = df.values
    # test_data = df_test.values
    train_data = house_prices.extract_numerical_features(df).values
    test_data = house_prices.extract_numerical_features(df_test).values


    is_simple_model = 0
    if is_simple_model:
        df_simple_model = house_prices.clean_data(df_publ)
        # df_simple_model = house_prices.prepare_data_random_forest(df_publ)

        # Prepare simple model
        df_test_simple_model = house_prices.extract_numerical_features(df_test_publ)
        is_remove_null = 0
        if is_remove_null:
            df_test_simple_model = df_test_simple_model.dropna(axis=1)
        else:
            df_test_simple_model = house_prices.estimate_by_mice(df_test_simple_model)

        df_simple_model = df_simple_model[df_test_simple_model.columns.insert(np.shape(df_test_simple_model.columns)[0], 'SalePrice')]


        train_data_simple = df_simple_model.values
        test_data_simple = df_test_simple_model.values
        x_train = train_data_simple[0::, :-1]
        y_train = train_data_simple[0::, -1]

        forest = RandomForestClassifier(max_features='sqrt')  #n_estimators=100)#, n_jobs=-1)#, max_depth=None, min_samples_split=2, random_state=0)#, max_features=np.sqrt(5))
        parameter_grid = {'max_depth': [4,5,6,7,8], 'n_estimators': [200,210,240,250],'criterion': ['gini', 'entropy']}
        cross_validation = StratifiedKFold(random_state=None, shuffle=False)  #, n_folds=10)
        grid_search = GridSearchCV(forest, param_grid=parameter_grid, cv=cross_validation, n_jobs=24)
        grid_search.fit(x_train, y_train)
        output = grid_search.predict(test_data_simple)
        print('Best score: {}'.format(grid_search.best_score_))
        print('Best parameters: {}'.format(grid_search.best_params_))






    ''' Explore data '''
    explore_data = 1
    if explore_data:

        is_missing_value_exploration = 0
        if is_missing_value_exploration:
            # Imputation for the 11 columns with none or nan values in the test data.
            # Using only numerical feature columns as first approach.
            # Print numeric feature columns with none or nan in test data
            print '\nColumns in train data with none/nan values:\n'
            print('\nTraining set numerical features\' missing values')
            df_publ_numerical_features = house_prices.extract_numerical_features(df_publ)
            house_prices.missing_values_in_DataFrame(df_publ_numerical_features)

            # Print numeric feature columns with none/nan in test data
            print '\nColumns in test data with none/nan values:\n'
            print('\nTest set numerical features\' missing values')
            df_test_publ_numerical_features = house_prices.extract_numerical_features(df_test_publ)
            house_prices.missing_values_in_DataFrame(df_test_publ_numerical_features)

            # Imputation method applied to numeric columns in test data with none/nan values
            print("Training set missing values after imputation")
            df_imputed = house_prices.estimate_by_mice(df_publ_numerical_features)
            house_prices.missing_values_in_DataFrame(df_imputed)
            print("Testing set missing values after imputation")
            df_test_imputed = house_prices.estimate_by_mice(df_test_publ_numerical_features)
            house_prices.missing_values_in_DataFrame(df_test_imputed)

            print('\nTotal Records for values: {}\n'.format(house_prices.df.count().sum() + house_prices.df_test.count().sum()))
            print('Total Records for missing values: {}\n'.format(house_prices.df.isnull().sum().sum() + house_prices.df_test.isnull().sum().sum()))

            print('Training set missing values')
            house_prices.missing_values_in_DataFrame(house_prices.df)

            print('Test set missing values')
            house_prices.missing_values_in_DataFrame(house_prices.df_test)

            print("\n=== AFTER IMPUTERS ===\n")
            print("=== Check for missing values in set ===")
            # Todo: fix the bug that "Total Records for missing values" stays unchanged while "Total Records for values" changes
            print('\nTotal Records for values: {}\n'.format(df.count().sum() + df_test.count().sum()))
            print('Total Records for missing values: {}\n'.format(df.isnull().sum().sum() + df_test.isnull().sum().sum()))

            # Overview of missing values in non numerical features
            print("Training set missing values")
            house_prices.missing_values_in_DataFrame(df)
            print("Testing set missing values")
            house_prices.missing_values_in_DataFrame(df_test)

            print("Training set with all non numerical features without missing values\n")
            df_all_non_numerical_features = house_prices.extract_non_numerical_features(df_publ)
            print df_all_non_numerical_features.count()
            # house_prices.missing_values_in_DataFrame(df)
            print("\nTesting set with all non numerical features without missing values\n")
            df_test_all_non_numerical_features = house_prices.extract_non_numerical_features(df_test_publ)
            print df_test_all_non_numerical_features.count()
            # house_prices.missing_values_in_DataFrame(df_test)




            # SalePrice square meter plot
            # Overview of data with histograms
            feature_to_plot = ['LotAreaSquareMeters', 'LotFrontage', 'MasVnrArea', 'GarageYrBlt']
            # feature_to_plot = ['YearBuilt', 'SalePrice', 'LotAreaSquareMeters', 'OverallCond', 'TotalBsmtSF']
            df_imputed_prepared = df_imputed.copy()
            house_prices.feature_engineering(df_imputed_prepared)
            bin_number = 25
            # df[df.LotAreaSquareMeters <= 2500.0][feature_to_plot].hist(bins=bin_number, alpha=.5)
            # df_imputed_prepared[df_imputed_prepared.LotAreaSquareMeters <= 2500.0][feature_to_plot].hist(bins=bin_number, alpha=.5)

            # We expect more houses to be sold in the summer. Which is also the case month MM, year YYYY.
            # Sale tops in juli
            # df[['MoSold', 'YrSold']].dropna().hist(bins='auto', alpha=.5)
            # plt.show()
            # plt.close()

        # Categorical plot with seaborn
        is_categorical_plot = 0
        if is_categorical_plot:
            # sns.countplot(y='MSZoning', hue='MSSubClass', data=df, palette='Greens_d')
            # plt.show()
            # sns.stripplot(x='SalePrice', y='MSZoning', data=df, jitter=True, hue='LandContour')
            # plt.show()
            # sns.boxplot(x='SalePrice', y='MSZoning', data=df, hue='MSSubClass')
            # plt.show()
            # sns.boxplot(x='SalePrice', y='MSZoning', data=df)
            # plt.show()
            sns.boxplot(x='SalePrice', y='Neighborhood', data=df)
            plt.show()
            sns.boxplot(x='SalePrice', y='SaleCondition', data=df)
            plt.show()

            # sns.violinplot(x='SalePrice', y='MSZoning', data=df)
            # plt.show()
            # sns.violinplot(x='SalePrice', y='Neighborhood', data=df)
            # plt.show()

            # Arbitrary estimate, using the mean by default.
            # It also uses bootstrapping to compute a confidence interval around the estimate and plots that using error bars
            sns.barplot(x='SalePrice', y='MSZoning', hue='LotShape', data=df)
            plt.show()
            sns.barplot(x='SalePrice', y='Neighborhood', data=df)#, hue='LotShape')
            plt.show()
            sns.barplot(x='SalePrice', y='SaleCondition', data=df)#, hue='LotShape')
            plt.show()

            # sns.pointplot(x='SalePrice', y='MSZoning', hue='LotShape', data=df,
            #               palette={"Reg": "g", "IR1": "m", "IR2": "b", "IR3": "r"}, markers=["^", "o", 'x', '<'], linestyles=["-", "--", '-.', ':'])
            # plt.show()

            # g = sns.PairGrid(df, x_vars=['SalePrice', 'LotArea'], y_vars=['MSZoning', 'Utilities', 'LotShape'], aspect=.75, size=3.5)
            # g.map(sns.violinplot, palette='pastel')
            # plt.show()

            # Quite slow
            # sns.swarmplot(x='MSZoning', y='MSSubClass', data=df, hue='LandContour')
            # plt.show()



        is_choose_optimal_regularization_param = 0
        if is_choose_optimal_regularization_param:
            # Choose optimal value for alpha (regularization parameter) in Lasso and Ridge
            x_train = train_data[0::, :-1]
            y_train = train_data[0::, -1]
            alphas = [0.05, 0.1, 0.3, 1, 3, 4, 10, 15, 30, 50, 75]

            ridge = RidgeCV(alphas=alphas)
            ridge.fit(x_train, y_train)
            alpha = ridge.alpha_
            print("Best Ridge alpha:", alpha)

            alphas_lasso = [1e-6, 1e-5, 0.00005, 0.0001, 0.0005, 0.001] #, 0.1, 1] #[1, 0.1, 0.001, 0.0005]
            lasso = LassoCV(alphas=alphas_lasso)
            lasso.fit(x_train, y_train)
            alpha = lasso.alpha_
            print("Best Lasso alpha:", alpha)

            cv_ridge = [house_prices.rmse_cv(Ridge(alpha=alpha), x_train, y_train).mean() for alpha in alphas]
            cv_ridge = pd.Series(np.expm1(cv_ridge), index=alphas)
            cv_ridge.plot(title = "Validation")
            plt.xlabel('alpha')
            plt.ylabel('rmse')
            plt.show()
            print "\nOptimal regularization parameter alpha has rmse = "
            print cv_ridge.min()

            # cv_lasso = [house_prices.rmse_cv(LassoCV(alphas=[alpha]), x_train, y_train).mean() for alpha in alphas_lasso]
            cv_lasso = [house_prices.rmse_cv(Lasso(alpha=alpha), x_train, y_train).mean() for alpha in alphas_lasso]
            cv_lasso = pd.Series(np.expm1(cv_lasso), index=alphas_lasso)
            cv_lasso.plot(title="Validation")
            plt.xlabel('alpha')
            plt.ylabel('rmse')
            plt.show()
            print "\nOptimal regularization parameter alpha has rmse = "
            print cv_lasso.min()

            print "\nMean lasso rmse:"
            model_lasso = LassoCV(alphas=[1, 0.1, 0.001, 0.0005]).fit(x_train, y_train)
            print house_prices.rmse_cv(model_lasso, x_train, y_train).mean()



    is_make_a_prediction = 1
    if is_make_a_prediction:
        ''' Random Forest '''
        # Fit the training data to the survived labels and create the decision trees
        X_train = train_data[0::, :-1]
        y_train = train_data[0::, -1]
        # x_train = np.asarray(x_train, dtype=long)
        # y_train = np.asarray(y_train, dtype=long)
        # test_data = np.asarray(test_data, dtype=long)

        # Todo: OBS. the below strategy with RandomForestClassifier produces best prediction 07.02.17
        # Random forest classifier based on cross validation parameter dictionary
        # Create the random forest object which will include all the parameters for the fit
        # forest = RandomForestClassifier(max_features='sqrt')  #n_estimators=100)#, n_jobs=-1)#, max_depth=None, min_samples_split=2, random_state=0)#, max_features=np.sqrt(5))
        # forest = RandomForestClassifier(n_estimators=210, n_jobs=-1, max_depth=4, min_samples_split=2, criterion='entropy') #, random_state=0)#, max_features=np.sqrt(5))
        # forest = RandomForestRegressor()
        # forest = SGDRegressor()
        # forest = Ridge(alpha=1.0)
        # Regularized linear regression is needed to avoid overfitting even if you have lots of features
        # lasso = Lasso(alpha=1e-4)
        lasso = LassoCV(alphas=[0.0001, 0.0003, 0.0006, 0.001, 0.003, 0.006, 0.01, 0.03, 0.06, 0.1,
                                0.3, 0.6, 1],
                        max_iter=50000, cv=10)
        # lasso = RidgeCV(alphas=[0.0001, 0.0003, 0.0006, 0.001, 0.003, 0.006, 0.01, 0.03, 0.06, 0.1,
        #                         0.3, 0.6, 1], cv=10)

        lasso.fit(X_train, y_train)
        alpha = lasso.alpha_
        print('best alpha:', alpha)

        # parameter_grid = {'max_depth': [4,5,6,7,8], 'n_estimators': [200,210,240,250]} #,'criterion': ['gini', 'entropy']}
        # cross_validation = StratifiedKFold(random_state=None, shuffle=False)  #, n_folds=10)
        # grid_search = GridSearchCV(forest, param_grid=parameter_grid, cv=cross_validation, n_jobs=24)
        grid_search = lasso
        # grid_search.fit(X_train, y_train)
        output = grid_search.predict(test_data)
        score = lasso.score(X_train, y_train)

        # print('Best score: {}'.format(grid_search.best_score_))
        # print('Best parameters: {}'.format(grid_search.best_params_))
        print '\nSCORE random forest train (grid search optim) data:---------------------------------------------------'
        print score

        is_feature_selection_prediction = 0
        if is_feature_selection_prediction:

            # Random forest (rf) classifier for feature selection
            forest_feature_selection = RandomForestClassifier()  #max_features='sqrt')#n_estimators=100)#, n_jobs=-1)#, max_depth=None, min_samples_split=2, random_state=0)#, max_features=np.sqrt(5))
            # forest_feature_selection = RandomForestRegressor(n_estimators=100)
            forest_feature_selection = forest_feature_selection.fit(x_train, y_train)
            # forest_feature_selection = forest_feature_selection.fit(np.asarray(x_train, dtype=long), np.asarray(y_train, dtype=long))
            output = forest_feature_selection.predict(test_data)
            # output = forest_feature_selection.predict(np.asarray(test_data, dtype=long))
            # print np.shape(output)
            score = forest_feature_selection.score(x_train, y_train)
            # score = forest_feature_selection.score(np.asarray(x_train, dtype=long), np.asarray(y_train, dtype=long))
            print '\nSCORE random forest train data:---------------------------------------------------'
            print score

            # print titanic_panda_inst.compute_score_crossval(forest_feature_selection, x_train, y_train)
            # Take the same decision trees and run it on the test data
            # output = forest_feature_selection.predict(test_data)

            # Evaluate variable importance with no cross validation
            importances = forest_feature_selection.feature_importances_
            std = np.std([tree.feature_importances_ for tree in forest_feature_selection.estimators_], axis=0)
            indices = np.argsort(importances)[::-1]

            print '\nFeatures:'
            df_test_num_features = house_prices.extract_numerical_features(df_test)
            print np.reshape(
                np.append(np.array(list(df_test_num_features)), np.arange(0, len(list(df_test_num_features)))),
                (len(list(df_test_num_features)), 2),
                'F')  # , 2, len(list(df_test)))

            print 'Feature ranking:'
            for f in range(x_train.shape[1]):
                print '%d. feature %d (%f)' % (f + 1, indices[f], importances[indices[f]])

            # Select most important features
            feature_selection_model = SelectFromModel(forest_feature_selection, prefit=True)
            x_train_new = feature_selection_model.transform(x_train)
            print x_train_new.shape
            # test_data_new = feature_selection_model.transform(test_data)
            # print test_data_new.shape
            # We get that four features are selected

            forest_feature_selected = forest_feature_selection.fit(x_train_new, y_train)
            score = forest_feature_selected.score(x_train_new, y_train)
            print '\nSCORE random forest train data (feature select):---------------------------------------------------'
            print score
            # print titanic_panda_inst.compute_score_crossval(forest, x_train_new, y_train)


        ''' xgboost '''
        is_xgb_simple = 0
        if is_xgb_simple:
            SEED = 0
            dtrain = xgb.DMatrix(x_train, label=y_train)
            dtest = xgb.DMatrix(test_data)

            xgb_params = {
                'seed': 0,
                'colsample_bytree': 0.8,
                'silent': 1,
                'subsample': 0.6,
                'learning_rate': 0.01,
                'objective': 'reg:linear',
                'max_depth': 1,
                'num_parallel_tree': 1,
                'min_child_weight': 1,
                'eval_metric': 'rmse',
            }

            res = xgb.cv(xgb_params, dtrain, num_boost_round=1000, nfold=4, seed=SEED, stratified=False,
                         early_stopping_rounds=25, verbose_eval=10, show_stdv=True)

            best_nrounds = res.shape[0] - 1
            cv_mean = res.iloc[-1, 0]
            cv_std = res.iloc[-1, 1]

            print('Ensemble-CV: {0}+{1}'.format(cv_mean, cv_std))

            gbdt = xgb.train(xgb_params, dtrain, best_nrounds)
            output = gbdt.predict(dtest)
            # score = gbdt.score(dtrain)
            # print '\nSCORE random forest train data (feature select):---------------------------------------------------'
            # print score
            # print '\nSCORE XGBRegressor train data:---------------------------------------------------'
            # print(gbdt.best_score_)
            # print(gbdt.best_params_)

        # Grid search xgb
        use_xgbRegressor = 0
        if use_xgbRegressor:
            # Is a parallel job
            # xgb_model = xgb.XGBRegressor()
            xgb_model = xgb.XGBRegressor(n_estimators = 360, max_depth = 2, learning_rate = 0.1)
            # XGBClassifier gives the best prediction
            # xgb_model = xgb.XGBClassifier()
            cross_validation = StratifiedKFold(shuffle=False, random_state=None)  # , n_folds=10)
            # parameter_grid = {'max_depth': [4, 5, 6, 7, 8], 'n_estimators': [200, 210, 240, 250]}
            parameter_grid = {'max_depth': [2, 4, 6], 'n_estimators': [50, 100, 200]}  #, 'criterion': ['gini', 'entropy']}
            clf = GridSearchCV(xgb_model, param_grid=parameter_grid, cv=cross_validation)  #verbose=1)
            clf.fit(x_train, y_train)
            output = clf.predict(test_data)
            print '\nSCORE XGBRegressor train data:---------------------------------------------------'
            print(clf.best_score_)
            print(clf.best_params_)


        # Early stopping, does not work
        # x_train_split, x_train_test, y_train_split, y_train_test = train_test_split(x_train, y_train)#, random_state=0)
        # print np.shape(x_train_split), np.shape(x_train_test), np.shape(y_train_split), np.shape(y_train_test)
        # Does not work
        # xgb_model_clf = xgb.XGBClassifier().fit(x_train_split, y_train_split, early_stopping_rounds=10, eval_metric='rmse', eval_set=[(x_train_split, y_train_split), (x_train_test, y_train_test)])
        # xgb_model_clf = xgb.XGBClassifier().fit(x_train, y_train)
        # output = xgb_model_clf.predict(test_data)
        # score = xgb_model_clf.score(x_train, y_train)
        # print '\nSCORE xgb train data:---------------------------------------------------'
        # print score

        # output = xgb_model.predict(test_data)
        # score = xgb_model.score(x_train, y_train)
        # print '\nSCORE xgb train data:---------------------------------------------------'
        # print score


    if is_simple_model or is_make_a_prediction:
        ''' Submission '''
        save_path = '/home/user/Documents/Kaggle/HousePrices/submission/'
        # Submission requires a csv file with Id and SalePrice columns.
        # dfBestScore = pd.read_csv(''.join([save_path, 'submission_house_prices.csv']), header=0)

        # We do not expect all to be equal since the learned model differs from time to time.
        # print (dfBestScore.values[0::, 1::].ravel() == output.astype(int))
        # print np.array_equal(dfBestScore.values[0::, 1::].ravel(), output.astype(int))  # But they are almost never all equal

        # Exp() is needed in order to get the correct sale price, since we took a log() earlier
        # if not is_simple_model:
        output = np.expm1(output) # - 1.0
        submission = pd.DataFrame({'Id': Id_df_test, 'SalePrice': output})
        submission.to_csv(''.join([save_path, 'submission_house_prices.csv']), index=False)

if __name__ == '__main__':
    main()