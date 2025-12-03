import pandas as pd
import json

# Read the original restaurants CSV
df = pd.read_csv("pasgo_restaurants_hcm.csv")

# Select only name & image_local_path columns
df_restaurant = df[['name', 'image_local_path']]

# Save to a new CSV
df_restaurant.to_csv("restaurants_pasgo_simple.csv", index=False)
print("New CSV created: restaurants_pasgo_simple.csv")

