import pyreadstat
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from sklearn.cluster import KMeans
import warnings
import random

# Ignore all warnings
warnings.simplefilter("ignore")

path = "your_path"

# Use this if you're using the SAS data file
# df, meta = pyreadstat.read_sas7bdat(path + 'all_data_2021apr.sas7bdat')
# df.to_excel('SAS Data.xlsx')
# Use this if you're using an excel version
df = pd.read_excel(path + "SAS Data.xlsx")
# print(df.columns)

# First, calculate how many values are not empty, and remove those measures that are scored at most 100 times
x = df.isnull().sum() # Get a Series that counts how many are empty

# Now make the series tell how many are not empty
for i in range(len(x)):
    x[i] = len(df) - x[i]

# Remove subsequent columns if they have <= 100 nonempty values
drop_cols = []
for i in range(len(x)):
    if x[i] <= 100:
        drop_cols.append(df.columns[i])

df.drop(columns = drop_cols, inplace = True)
del(drop_cols)
del(x)

# Now make groups
# Mortality measures
mort = ["MORT_30_AMI", "MORT_30_CABG", "MORT_30_COPD", "MORT_30_HF", "MORT_30_PN", "MORT_30_STK", "PSI_4_SURG_COMP"]

# Safety of Care measures
safety = ["HAI_1", "HAI_2", "HAI_3", "HAI_4", "HAI_5", "HAI_6", "COMP_HIP_KNEE", "PSI_90_SAFETY"]

# Readmission measures
readmit = ["READM_30_CABG", "READM_30_COPD", "READM_30_HIP_KNEE", "READM_30_HOSP_WIDE", "EDAC_30_AMI", "EDAC_30_HF", "EDAC_30_PN", "OP_32", "OP_35_ADM", "OP_35_ED", "OP_36"]

# Patient Experience measures
pat_exp = ["H_COMP_1_STAR_RATING", "H_COMP_2_STAR_RATING", "H_COMP_3_STAR_RATING", "H_COMP_5_STAR_RATING", "H_COMP_6_STAR_RATING", "H_COMP_7_STAR_RATING", "H_RESP_RATE_P", "H_NUMB_COMP"]

# Timely and Effective Care measures
time = ["IMM_3", "OP_10", "OP_13", "OP_18B", "OP_22", "OP_23", "OP_29", "OP_33", "OP_3B", "OP_8", "PC_01", "SEP_1"]

# Now only keep the columns that are in the groups, and the provider ID
df = df[["PROVIDER_ID"] + mort + safety + readmit + pat_exp + time]

# Now standardize everything
for i in mort + safety + readmit + pat_exp + time:
    df[i] = (df[i] - df[i].mean()) / df[i].std()

# Now switch the direction of certain measures
for i in mort + readmit + ["OP_22", "PC_01", "OP_8", "OP_10", "OP_13"]:
    df[i] = (-1) * df[i]

# Now get row means to get group scores
df['MORT'] = df[mort].mean(axis = 1)
df['SAFETY'] = df[safety].mean(axis = 1)
df['READMIT'] = df[readmit].mean(axis = 1)
df['PAT_EXP'] = df[pat_exp].mean(axis = 1)
df['TIME'] = df[time].mean(axis = 1)

# Hospitals must report at least 3 measures with at least 3 measure groups (mortality and safety must be at least one of them)
# Replace the respective group measure score with "nan" if its count is < 3
df['MORT'].where(df[mort].count(axis = 1) >= 3, inplace = True)
df['SAFETY'].where(df[safety].count(axis = 1) >= 3, inplace = True)
df['READMIT'].where(df[readmit].count(axis = 1) >= 3, inplace = True)
df['PAT_EXP'].where(df[pat_exp].count(axis = 1) >= 3, inplace = True)
df['TIME'].where(df[time].count(axis = 1) >= 3, inplace = True)

# Drop everything except the measure groups and Provider ID (this may be better done by making a new dataframe, if you still want to see all of the scores, I just do this for runtime complexity and simplicity)
df = df[["PROVIDER_ID", 'MORT', 'SAFETY', 'READMIT', 'PAT_EXP', 'TIME']]
# print(df.columns)

# Now figure out how many stars a facility can receive
df['STARS'] = df[['MORT', 'SAFETY', 'READMIT', 'PAT_EXP', 'TIME']].count(axis = 1)

# Get rid of facilities where the stars are less than 3
df = df[df['STARS'] >= 3]

# Make sure they have either mortality or safety of care
# Make empty binary dataset
df_na = df.isna()
df = df[(df_na['MORT'] != True) | (df_na['SAFETY'] != True)]
del(df_na)

# Now create separate dataframes based on star possibility
df3 = df[df['STARS'] == 3]
df4 = df[df['STARS'] == 4]
df5 = df[df['STARS'] == 5]

# Now standardize all group measures
for i in ['MORT', 'SAFETY', 'READMIT', 'PAT_EXP', 'TIME']:
    df5[i] = (df5[i] - df5[i].mean()) / df5[i].std()

# Now calculate the weighted summary scores
df5['SUMMARY'] = (0.22 * df5.MORT) + (0.22 * df5.SAFETY) + (0.22 * df5.READMIT) + (0.22 * df5.PAT_EXP) + (0.12 * df5.TIME)

# Set the initial centroids to the medians of the quantiles
# First get cutoffs of the quantiles
df5 = df5.sort_values(by = ['SUMMARY'])
x1 = (len(df5) // 5)
x2 = (len(df5) // 5) * 2
x3 = (len(df5) // 5) * 3
x4 = (len(df5) // 5) * 4
c1 = df5['SUMMARY'][:x1].median()
c2 = df5['SUMMARY'][x1:x2].median()
c3 = df5['SUMMARY'][x2:x3].median()
c4 = df5['SUMMARY'][x3:x4].median()
c5 = df5['SUMMARY'][x4:].median()

centroids = np.array([c1, c2, c3, c4, c5])
centroids = centroids.reshape(-1, 1) # Shape it to work in function
del(x1, x2, x3, x4, df) # Clear space
data = np.array(df5['SUMMARY'])
data = data.reshape(-1, 1)

random.seed(1)
k5 = KMeans(n_clusters = 5, init = centroids, max_iter = 1000, n_init = 1)
pred = k5.fit_predict(data)
pred += 1 # Predictions are 0-4, rescale for 1-5
df5.loc[:, 'RANK'] = pred.tolist()

# Get some summary stats

# Table with value counts of ranks, ranges, and center / average
print(df5['RANK'].value_counts().sort_index().to_markdown())
for i in range(1, 6):
    print(i)
    print(df5.RANK.value_counts()[i])
    print(round(df5.RANK.value_counts()[i] / len(df5.RANK) * 100, 1), "%", sep = "")
    print("Min =", round(min(df5.SUMMARY[df5.RANK == i]), 3))
    print("Max =", round(max(df5.SUMMARY[df5.RANK == i]), 3))
    print("Average =", round(df5.SUMMARY[df5.RANK == i].mean(), 3))
    print("\n")

# Bar chart of rankings

# Get Your Facility Ranking, Summary Score, and Group Scores
for i in ['RANK', 'SUMMARY', 'MORT', 'SAFETY', 'READMIT', 'PAT_EXP', 'TIME']:
    print(i)
    print(df5[i][df5['PROVIDER_ID'] == 111111],"\n") # Facility ID goes here

# Get the 5-Star facilities averages
for i in ['MORT', 'SAFETY', 'READMIT', 'PAT_EXP', 'TIME']:
    print(i)
    print("Average =", round(df5[i][df5.RANK == 5].mean(), 3), "\n")

# Histogram of summary scores with divider lines for star ratings
plt.hist(df5['SUMMARY'], bins = 12)
plt.title("Distribution of Summary Scores")
plt.savefig(path + "Distribution of Summary Scores.png")
plt.show()

# Bar chart of distribution of rankings
ranks = list(range(1, 6))
values = []
for i in ranks:
    values.append(df5.RANK.value_counts()[i])
plt.bar(ranks, height = values)
plt.title("Distribution of Rankings (out of 5)")
plt.savefig(path + "Distribution of Star Ratings.png")
plt.show()
