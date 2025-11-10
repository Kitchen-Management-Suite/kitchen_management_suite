## 📦 API Response Schema

### Endpoint
Output of ```searchRawIntregient(itemName)```
Contained in root/src/helpers/api_helper.py <br>
Connected to USDA API, 1000 request limit per minute <br>
Takes optional keyword arguments page_size & page <br>
By default page_size = 100 & page = 1 <br>
API Documentation may be found at [USDA FoodData Central](https://fdc.nal.usda.gov/)


### Example Response Top level

```json
{
  "totalHits": 51408,
  "currentPage": 1,
  "totalPages": 51408,
  "pageList": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  "foodSearchCriteria": { ... },
  "foods": [ { ... } ],
  "aggregations": { ... }
}

````

### Example Food Object

```json
{
  "fdcId": 577532,
  "description": "EGGS",
  "dataType": "Branded",
  "gtinUpc": "021130049134",
  "brandOwner": "Safeway, Inc.",
  "foodCategory": "Eggs & Egg Substitutes",
  "servingSize": 44.0,
  "servingSizeUnit": "g",
  "householdServingFullText": "1 EGG",
  "foodNutrients": [ ... ]
}
```

### Example foodNutrients Object 

```json
  {
    "nutrientId": 1003,
    "nutrientName": "Protein",
    "nutrientNumber": "203",
    "unitName": "G",
    "value": 13.6,
    "percentDailyValue": 12,
    "derivationCode": "LCCS",
    "derivationDescription": "Calculated from value per serving size measure",
    "foodNutrientSourceDescription": "Manufacturer's analytical; partial documentation"
  }
```

