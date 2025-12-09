## 📦 API Response Schema

### Endpoint
Output of ```searchByStr(searchText)```
Contained in root/src/helpers/api_helper.py <br>
Takes optional keyword arguments page_size & page <br>
By default page_size = 100 & page = 1 <br>
API Documentation may be found at [Product Opener (Open Food Facts Server)](https://openfoodfacts.github.io/openfoodfacts-server/api/)


### Example Response Top level

```json
{
  "count": 10000,
  "page": 1,
  "page_count": 1,
  "page_size": 560,
  "products": [{ ... }], //List of size count which contains every product as a dictionary of 255 attributes
  "skip": 0
}
```

### The 255 Attributes of Each Product Object
For posterity there are 255 attributes of each product. <br>
The most import attribute for our purposes in nutriments <br>
See below for the nutriments scheme <br> 
(Actual values are not null, obviously)
```json
{
  "_id": null,
  "_keywords": null,
  "added_countries_tags": null,
  "additives_n": null,
  "additives_original_tags": null,
  "additives_tags": null,
  "allergens": null,
  "allergens_from_ingredients": null,
  "allergens_from_user": null,
  "allergens_hierarchy": null,
  "allergens_lc": null,
  "allergens_tags": null,
  "amino_acids_prev_tags": null,
  "amino_acids_tags": null,
  "brands": null,
  "brands_tags": null,
  "categories": null,
  "categories_hierarchy": null,
  "categories_lc": null,
  "categories_old": null,
  "categories_properties": null,
  "categories_properties_tags": null,
  "categories_tags": null,
  "category_properties": null,
  "checkers_tags": null,
  "ciqual_food_name_tags": null,
  "cities_tags": null,
  "code": null,
  "codes_tags": null,
  "compared_to_category": null,
  "complete": null,
  "completeness": null,
  "correctors_tags": null,
  "countries": null,
  "countries_beforescanbot": null,
  "countries_hierarchy": null,
  "countries_lc": null,
  "countries_tags": null,
  "created_t": null,
  "creator": null,
  "data_quality_bugs_tags": null,
  "data_quality_completeness_tags": null,
  "data_quality_dimensions": null,
  "data_quality_errors_tags": null,
  "data_quality_info_tags": null,
  "data_quality_tags": null,
  "data_quality_warnings_tags": null,
  "data_sources": null,
  "data_sources_tags": null,
  "debug_param_sorted_langs": null,
  "ecoscore_data": null,
  "ecoscore_grade": null,
  "ecoscore_tags": null,
  "editors": null,
  "editors_tags"_
}
```

### Example Nutriments Scheme

```json
{
  "carbohydrates": 28,
  "carbohydrates_100g": 28,
  "carbohydrates_serving": 28,
  "carbohydrates_unit": "g",
  "carbohydrates_value": 28,
  "carbon-footprint-from-known-ingredients_100g": 72.8,
  "carbon-footprint-from-known-ingredients_product": 146,
  "carbon-footprint-from-known-ingredients_serving": 72.8,
  "energy": 1155,
  "energy-kcal": 275,
  "energy-kcal_100g": 275,
  "energy-kcal_serving": 275,
  "energy-kcal_unit": "kcal",
  "energy-kcal_value": 275,
  "energy-kcal_value_computed": 275.4,
  "energy-kj": 1155,
  "energy-kj_100g": 1155,
  "energy-kj_serving": 1160,
  "energy-kj_unit": "kJ",
  "energy-kj_value": 1155,
  "energy-kj_value_computed": 1154.6,
  "energy_100g": 1155,
  "energy_serving": 1160,
  "energy_unit": "kJ",
  "energy_value": 1155,
  "fat": 12,
  "fat_100g": 12,
  "fat_serving": 12,
  "fat_unit": "g",
  "fat_value": 12,
  "fiber": 1.7,
  "fiber_100g": 1.7,
  "fiber_serving": 1.7,
  "fiber_unit": "g",
  "fiber_value": 1.7,
  "fruits-vegetables-legumes-estimate-from-ingredients_100g": 0,
  "fruits-vegetables-legumes-estimate-from-ingredients_serving": 0,
  "fruits-vegetables-nuts-estimate-from-ingredients_100g": 0.5,
  "fruits-vegetables-nuts-estimate-from-ingredients_serving": 0.5,
  "nova-group": 4,
  "nova-group_100g": 4,
  "nova-group_serving": 4,
  "nutrition-score-fr": 13,
  "nutrition-score-fr_100g": 13,
  "proteins": 13,
  "proteins_100g": 13,
  "proteins_serving": 13,
  "proteins_unit": "g",
  "proteins_value": 13,
  "salt": 1.2,
  "salt_100g": 1.2,
  "salt_serving": 1.2,
  "salt_unit": "g",
  "salt_value": 1.2,
  "saturated-fat": 5.9,
  "saturated-fat_100g": 5.9,
  "saturated-fat_serving": 5.9,
  "saturated-fat_unit": "g",
  "saturated-fat_value": 5.9,
  "sodium": 0.48,
  "sodium_100g": 0.48,
  "sodium_serving": 0.48,
  "sodium_unit": "g",
  "sodium_value": 0.48,
  "sugars": 2.9,
  "sugars_100g": 2.9,
  "sugars_serving": 2.9,
  "sugars_unit": "g",
  "sugars_value": 2.9
}
```