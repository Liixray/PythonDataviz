import pandas as pds


def cleanDataset() -> None:
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
    cleanWorldEducationData.to_csv(
        "data/cleaned/cleaned-world-education-data.csv", index=False
    )
