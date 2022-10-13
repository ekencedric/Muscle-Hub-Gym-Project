#Project: MuscleHub AB Test


# This import only needs to happen once, at the beginning of the notebook
from codecademySQL import sql_query #adjust this
import pandas as pd
from matplotlib import pyplot as plt
from scipy.stats import chi2_contingency

# Displaying the data
sql_query('''
SELECT *
FROM visits
LIMIT 5
''')

# Save the data to a DataFrame
df = sql_query('''
SELECT *
FROM applications
LIMIT 5
''')

# - `visits` contains information about potential gym customers who have visited MuscleHub
# - `fitness_tests` contains information about potential customers in "Group A", who were given a fitness test
# - `applications` contains information about any potential customers (both "Group A" and "Group B") who filled out an application.  Not everyone in `visits` will have filled out an application.
# - `purchases` contains information about customers who purchased a membership to MuscleHub.

# Examining visits 
sql_query('''
SELECT *
FROM visits
LIMIT 5
''')
# Examining fitness_tests 
sql_query('''
SELECT *
FROM fitness_tests
LIMIT 5
''')
# Examining applications 
sql_query('''
SELECT *
FROM applications
LIMIT 5
''')
# Examining purchases 
sql_query('''
SELECT *
FROM purchases
LIMIT 5
''')

# 1. Not all visits in  `visits` occurred during the A/B test.  Data is pulled where `visit_date` is on or after `7-1-17`.
# 
# 2. Performing `LEFT JOIN` commands to combine the four tables.  Performing joins on `first_name`, `last_name`, and `email` to get useful columns for the analysis

df = sql_query('''
SELECT visits.first_name,
       visits.last_name,
       visits.visit_date,
       fitness_tests.fitness_test_date,
       applications.application_date,
       purchases.purchase_date
FROM visits
LEFT JOIN fitness_tests
    ON fitness_tests.first_name = visits.first_name
    AND fitness_tests.last_name = visits.last_name
    AND fitness_tests.email = visits.email
LEFT JOIN applications
    ON applications.first_name = visits.first_name
    AND applications.last_name = visits.last_name
    AND applications.email = visits.email
LEFT JOIN purchases
    ON purchases.first_name = visits.first_name
    AND purchases.last_name = visits.last_name
    AND purchases.email = visits.email
WHERE visits.visit_date >= '7-1-17'
''')

# Adding column `ab_test_group` to df. Value is `A` if `fitness_test_date` is not `None`, and `B` if `fitness_test_date` is `None`.

df['ab_test_group'] = df.fitness_test_date.apply(lambda x:
                                                'A' if pd.notnull(x) else 'B')

# Counting how many users are in each `ab_test_group`.  

ab_counts = df.groupby('ab_test_group').first_name.count().reset_index()
print(ab_counts)

# Observing ab_counts dataframe on a piechart

plt.pie(ab_counts.first_name.values, labels=['A', 'B'], autopct='%0.2f%%')
plt.axis('equal')
plt.show()
plt.savefig('ab_test_pie_chart.png')

# The sign-up process for MuscleHub has several steps:
# 1. Take a fitness test with a personal trainer (only Group A)
# 2. Fill out an application for the gym
# 3. Send in their payment for their first month's membership
# 
# Examining how many people make it to Step 2, filling out an application.
# 
# Creating a new column in `df` called `is_application` which is `Application` if `application_date` is not `None` and `No Application`, otherwise.
df['is_application'] = df.application_date.apply(lambda x: 'Application'
                                                  if pd.notnull(x) else 'No Application')

# Counting how many people from Group A and Group B either do or don't pick up an application.  
app_counts = df.groupby(['ab_test_group', 'is_application']).first_name.count().reset_index()

# Calculating the percent of people in each group who complete an application by pivoting `app_counts` such that:
# - The `index` is `ab_test_group`
# - The `columns` are `is_application`
app_pivot = app_counts.pivot(columns='is_application',
                            index='ab_test_group',
                            values='first_name')\
            .reset_index()
print(app_pivot)

# Creating a column called `Total`, which is the sum of `Application` and `No Application`.

app_pivot['Total'] = app_pivot.Application + app_pivot['No Application']

app_pivot['Percent with Application'] = app_pivot.Application / app_pivot.Total

# It looks like more people from Group B turned in an application.  Why might that be?
# 
# Determining if this difference is statistically significant.
# 
# Performing a hypothesis test to determine statistical significance and saving p-value

contingency = [[250, 2254], [325, 2175]]
chi2_contingency(contingency)

# Determining  how many purchased a membership among those who picked up an application
#
# Adding a column to `df` called `is_member` which is `Member` if `purchase_date` is not `None`, and `Not Member` otherwise.

df['is_member'] = df.purchase_date.apply(lambda x: 'Member' if pd.notnull(x) else 'Not Member')

# Creating a DataFrame called `just_apps` that contains only people who picked up an application.

just_apps = df[df.is_application == 'Application']

# Finding out how many people in `just_apps` are and aren't members from each group.  

member_count = just_apps.groupby(['ab_test_group', 'is_member']).first_name.count().reset_index()
member_pivot = member_count.pivot(columns='is_member',
                                  index='ab_test_group',
                                  values='first_name')\
                           .reset_index()

member_pivot['Total'] = member_pivot.Member + member_pivot['Not Member']
member_pivot['Percent Purchase'] = member_pivot.Member / member_pivot.Total

# It looks like people who took the fitness test were more likely to purchase a membership **if** they picked up an application.  Why might that be?
# 
# Performing a hypothesis test to determine if this difference is statistically significant.  

contingency = [[200, 50], [250, 75]]
chi2_contingency(contingency)

# Determining the percentage of all visitors purchased memberships. 
final_member_count = df.groupby(['ab_test_group', 'is_member']).first_name.count().reset_index()
final_member_pivot = final_member_count.pivot(columns='is_member',
                                  index='ab_test_group',
                                  values='first_name')\
                           .reset_index()

final_member_pivot['Total'] = final_member_pivot.Member + final_member_pivot['Not Member']
final_member_pivot['Percent Purchase'] = final_member_pivot.Member / final_member_pivot.Total

# It was previously observed that, when only people who had **already picked up an application** were considered, 
# there was no significant difference in membership between Group A and Group B.
# 
# Now, when considering all people who **visit MuscleHub**, there might be a significant different in memberships between Group A and Group B. Performing a hypothesis test to verify
contingency = [[200, 2304], [250, 2250]]
chi2_contingency(contingency)

# ## Step 5: Summarize the acquisition funel with a chart

# Creating a bar chart that shows the difference between Group A (people who were given the fitness test) and Group B (people who were not given the fitness test) at each state of the process:
# - Percent of visitors who apply
# - Percent of applicants who purchase a membership
# - Percent of visitors who purchase a membership
# 
# Creating a plot for **each** of the three sets of percentages that were calculated in `app_pivot`, `member_pivot` and `final_member_pivot`.  

# Percent of Visitors who Apply
ax = plt.subplot()
plt.bar(range(len(app_pivot)),
       app_pivot['Percent with Application'].values)
ax.set_xticks(range(len(app_pivot)))
ax.set_xticklabels(['Fitness Test', 'No Fitness Test'])
ax.set_yticks([0, 0.05, 0.10, 0.15, 0.20])
ax.set_yticklabels(['0%', '5%', '10%', '15%', '20%'])
plt.show()
plt.savefig('percent_visitors_apply.png')

# Percent of Applicants who Purchase
ax = plt.subplot()
plt.bar(range(len(member_pivot)),
       member_pivot['Percent Purchase'].values)
ax.set_xticks(range(len(app_pivot)))
ax.set_xticklabels(['Fitness Test', 'No Fitness Test'])
ax.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1])
ax.set_yticklabels(['0%', '10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '90%', '100%'])
plt.show()
plt.savefig('percent_apply_purchase.png')

# Percent of Visitors who Purchase
ax = plt.subplot()
plt.bar(range(len(final_member_pivot)),
       final_member_pivot['Percent Purchase'].values)
ax.set_xticks(range(len(app_pivot)))
ax.set_xticklabels(['Fitness Test', 'No Fitness Test'])
ax.set_yticks([0, 0.05, 0.10, 0.15, 0.20])
ax.set_yticklabels(['0%', '5%', '10%', '15%', '20%'])
plt.show()
plt.savefig('percent_visitors_purchase.png')

