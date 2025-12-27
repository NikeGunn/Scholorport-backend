"""
Script to merge all university JSON data files and add apply_url to existing entries.
"""
import json
import os

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load existing data.json
with open(os.path.join(BASE_DIR, 'data.json'), 'r', encoding='utf-8') as f:
    existing_data = json.load(f)

print(f"Existing universities: {len(existing_data)}")

# Add apply_url to existing entries that don't have it
for uni in existing_data:
    if 'apply_url' not in uni:
        # Generate a default apply_url based on university name
        uni_name = uni.get('university_name', '').lower()
        # Create a search URL for universities without specific apply_url
        uni['apply_url'] = f"https://www.google.com/search?q={uni_name.replace(' ', '+')}+apply+admissions"

# Load new European data files
new_data_files = [
    'data_europe_uk.json',
    'data_europe_continent.json', 
    'data_europe_south_east.json'
]

new_universities = []
for filename in new_data_files:
    filepath = os.path.join(BASE_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            new_universities.extend(data)
            print(f"Loaded {len(data)} universities from {filename}")

# Get existing university names for deduplication
existing_names = {uni['university_name'].lower() for uni in existing_data}

# Add new universities that don't already exist
added_count = 0
for uni in new_universities:
    if uni['university_name'].lower() not in existing_names:
        existing_data.append(uni)
        existing_names.add(uni['university_name'].lower())
        added_count += 1

print(f"\nAdded {added_count} new universities")
print(f"Total universities now: {len(existing_data)}")

# Save merged data
output_path = os.path.join(BASE_DIR, 'data.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(existing_data, f, indent=2, ensure_ascii=False)

print(f"\nSaved merged data to {output_path}")

# Print summary by region
regions = {}
for uni in existing_data:
    region = uni.get('region', 'Unknown')
    regions[region] = regions.get(region, 0) + 1

print("\nUniversities by region:")
for region, count in sorted(regions.items(), key=lambda x: -x[1]):
    print(f"  {region}: {count}")

# Print summary by country
countries = {}
for uni in existing_data:
    country = uni.get('country', 'Unknown')
    countries[country] = countries.get(country, 0) + 1

print("\nUniversities by country:")
for country, count in sorted(countries.items(), key=lambda x: -x[1]):
    print(f"  {country}: {count}")
