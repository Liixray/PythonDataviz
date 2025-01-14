import pandas as pds
import kaggle

def downloadAndCleanDataset() -> None:
    # Download the raw dataset
    kaggle.api.authenticate()
    kaggle.api.dataset_download_files(
        "bushraqurban/world-education-dataset", path="data/raw", unzip=True
    )

    # Add continent informations to the default dataset
    rawCountryContinentData = pds.read_csv(
        "data/raw/country-and-continent-codes-list.csv"
    )
    rawWorldEducationData = pds.read_csv("data/raw/world-education-data.csv")
    cleanWorldEducationData = pds.merge(
        rawWorldEducationData,
        rawCountryContinentData[["Continent_Name", "Three_Letter_Country_Code"]],
        left_on="country_code",
        right_on="Three_Letter_Country_Code",
    )
    cleanWorldEducationData.to_csv("data/cleaned/cleaned-world-education-data.csv", index=False)
