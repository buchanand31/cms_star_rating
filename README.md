The Centers for Medicare and Medicaid Services (CMS) provides a star rating for eligible hospitals in the US based on their performance on certain metrics. Elibible hospitals must have at least 3 measures for at least 3 measure groups, and mortality and safety of care must be at last one of these measure groups. The details of the algorithm are noted below, but hospitals can be scored on either 3, 4, or 5 stars, depending on how many group measures they have.
CMS partnered with Yale to develop a SAS code that can be run to show hospital rankings, standardized values, and more, however I have found these SAS files difficult to run, and they seem to be problematic, as their logic seems mixed up with the documentation they provide, leaving those of us who can't read SAS in the dust.
I recreated their algorithm (results have NOT been verified against theirs since I can't get their SAS code to run) using R and Python. The code does copy over the saved dataframe, so the end result will not include everything and anything, however some minor tweaks and renamings can mek this better.

In essence, the algorithm standardizes all measures (flips the z-score to reflect "better" correctly [for example; a higher mortality rate should result in a lower z-score]), then adds measures up to get a group score, standardizes the group scores, adds them up (with certain weighting) to get a summary score, then perform k-means clustering to get 3, 4, or 5 groups, based on how many stars a facility can receive.

I only ran this model for 5-star facilities, as that is how many stars UPMC PUH/SHY can receive.

[Model Summary]
Steps for the Algorithm
1.	After loading in the data, I removed any measures that were reported in less than 100 hospitals.
a.	OP-02 was reported only 90 times, so it was removed.
2.	Create categories for groups (mortality, safety of care, readmission, patient experience, and timely and effective care).
3.	Next, standardize all measures.
a.	Switch the direction for all mortality, and readmission measures, as well as OP-22, PC-01, OP-8, OP-10, and OP-13.
i.	This ensures that “more” mortalities doesn’t give a higher score.
4.	Now get group measures scores by averaging all measures in the groups.
a.	Get rid of group scores if a group has less than 3 measures used.
5.	Now determine how many stars (groups) each hospital has, and only keep those that have at least 3 possible stars, and at least one has to be either mortality or readmission.
6.	Standardize group measures scores.
7.	Calculate weighted summary scores based on the CMS methodology.
8.	Run k-means clustering algorithm.
a.	Pick initial centroids to be the medians of the quantiles
b.	1,000 iterations

[Foolish Assumptions]
•	Hospitals must display at least 3 measures within at least 3 measure scores. Does this mean that each hospital must have at least 3 measurements for a measure group score to count?
•	In the methodology, they do not specify whether the group measure scores are standardized based on how many stars the hospitals can receive, or whether an aggregate standardization is done across all hospitals, regardless of their star potential status
o	I did my algorithm for the former, as that appears to be what they did, but that does not make much sense to me.
