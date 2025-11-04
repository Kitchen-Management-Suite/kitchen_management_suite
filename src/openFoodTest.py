from openfoodfacts import ProductDataset

dataset = ProductDataset(dataset_type="csv")

for product in dataset:
    print(product)