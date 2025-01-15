import kaggle


def downloadDataset() -> None:
    # Download the raw dataset
    kaggle.api.authenticate()
    kaggle.api.dataset_download_files(
        "bushraqurban/world-education-dataset", path="data/raw", unzip=True
    )
