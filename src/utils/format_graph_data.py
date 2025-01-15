import pandas as pds
import numpy as np


def getMapData(
    baseData: pds.DataFrame, year: int, displayPrimary: bool
) -> tuple[pds.DataFrame, int]:
    columnName = (
        "pupil_teacher_primary" if displayPrimary else "pupil_teacher_secondary"
    )
    worldEducationForMap = baseData[
        (baseData[columnName].notna()) & (baseData["year"] <= year)
    ]
    worldEducationForMap = worldEducationForMap.sort_values(
        by=["country", "year"], ascending=[True, False]
    )
    worldEducationForMap = worldEducationForMap.drop_duplicates(
        subset="country", keep="first"
    )
    maxPupilTeacher = worldEducationForMap[columnName].max()
    return worldEducationForMap, maxPupilTeacher


def getContinentEducationData(baseData: pds.DataFrame, year: int) -> pds.DataFrame:
    continentEducationData = baseData[
        (baseData["gov_exp_pct_gdp"].notna()) & (baseData["year"] <= year)
    ]
    continentEducationData = continentEducationData.sort_values(
        by=["country", "year"], ascending=[True, False]
    )
    continentEducationData = continentEducationData.drop_duplicates(
        subset="country", keep="first"
    )
    return (
        continentEducationData.groupby("Continent_Name")["gov_exp_pct_gdp"]
        .mean()
        .reset_index()
    )


def getBubbleData(baseData: pds.DataFrame, year: int) -> pds.DataFrame:
    bubbleData = baseData[baseData["year"] == year]
    bubbleData.loc[:, "gov_exp_pct_gdp"] = (
        bubbleData["gov_exp_pct_gdp"].fillna(0).astype(float)
    )
    return bubbleData


def getCorrelationData(baseData: pds.DataFrame) -> pds.DataFrame:
    renamed_columns = {
        "school_enrol_primary_pct": "Scolarisation en primaire",
        "school_enrol_secondary_pct": "Scolarisation en secondaire",
        "school_enrol_tertiary_pct": "Scolarisation en tertiaire",
        "pupil_teacher_primary": "Encadrement en primaire",
        "pupil_teacher_secondary": "Encadrement en secondaire",
        "lit_rate_adult_pct": "Alphabétisation des adultes",
        "pri_comp_rate_pct": "Réussite du cycle primaire",
        "gov_exp_pct_gdp": "PIB investi dans l'éducation",
    }
    baseData = baseData.rename(columns=renamed_columns, index=renamed_columns)
    # corrData =
    dataTypes = baseData.drop(columns=["year"]).select_dtypes(include=[np.number])
    # .drop(baseData.columns[baseData.columns.str.contains('unnamed',case = True)])
    correlationData = dataTypes.corr().round(2)
    return correlationData
