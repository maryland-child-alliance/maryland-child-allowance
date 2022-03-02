import pandas as pd
import numpy as np
import microdf as mdf
import plotly.express as px
from pathlib import Path
import os
import sys
from clean_data import format_census_geo_col

# Get the current working directory
cwd = os.getcwd()


def read_spm_person_stata(filepath_or_buffer):

    # Read in the spm person data if it is from a URL
    if filepath_or_buffer.startswith("http"):
        spm_person = pd.read_stata(
            filepath_or_buffer,
            columns=[
                "serialno",
                "sporder",
                "wt",
                "age",
                "spm_id",
                "spm_povthreshold",
                "spm_resources",
                "st",
                "puma",
            ],
        )
    # Read in the spm person data if it is from a local file
    else:
        filepath_or_buffer = Path(filepath_or_buffer)
        spm_person = pd.read_stata(
            filepath_or_buffer,
            columns=[
                "serialno",
                "sporder",
                "wt",
                "age",
                "spm_id",
                "spm_povthreshold",
                "spm_resources",
                "st",
                "puma",
            ],
        )
    return spm_person


def make_acs_md_county_df(filepath_or_buffer=None):
    """

    reads in the spm person data and makes a dataframe with the following columns:
    ['total_pov_change',
    'child_pov_change',
    'young_child_pov_change',
    'baby_pov_change',
    'population',
    'child_population',
    'young_child_population',
    'baby_population',
    'total_pov_rate',
    'child_pov_rate',
    'young_child_pov_rate',
    'baby_pov_rate',
    'new_total_pov_rate',
    'new_child_pov_rate',
    'new_young_child_pov_rate',
    'new_baby_pov_rate',]
    parameters
    ----------
    filepath_or_buffer: str
        path or url to the spm person data in stata .dta format
    """

    # Read in the spm person data
    if spm_person_stata_path:
        spm_person_stata_path = Path(spm_person_stata_path)
        person = read_spm_person_stata(spm_person_stata_path)
    else:
        person = read_spm_person_stata(
            "https://www2.census.gov/programs-surveys/supplemental-poverty-measure/datasets/spm/spm_2019_pu.dta",
        )

    # Cleanup
    person.columns = person.columns.str.lower()
    person = person.rename(columns={"serialno": "serial", "sporder": "pernum"})

    person = person.astype(
        {
            "serial": "int",
            "pernum": "int",
            "wt": "int",
            "age": "int",
            "spm_id": "int",
            "spm_povthreshold": "int",
            "spm_resources": "int",
        }
    )

    # Sort to just Maryland
    person = person[person["st"] == 24]

    # assign random district
    person["district"] = np.random.randint(1, 48, person.shape[0])

    # Assign random county
    person["county"] = np.random.randint(1, 25, person.shape[0])

    # Replace NIUs
    person = person.replace(9999999, 0)

    # Define age groups
    person["child"] = person.age < 18
    person["young_child"] = person.age < 5
    person["baby"] = person.age == 0

    # Use groupby to calculate total babies, young children, and children in each spm unit
    spmu = person.groupby(["spm_id"])[["child", "young_child", "baby"]].sum()
    spmu.columns = ["spm_children", "spm_young_children", "spm_babies"]
    # merge back onto the person dataframe
    person = person.merge(spmu, left_on=["spm_id"], right_index=True)

    # Consider three reforms
    # 1 a $100 universal child allowance (0-17)
    # 2 a $100 universal young child allowance (0-4)
    # 3 a $1,000 baby bonus given upon the birth of a child

    def pov(reform, district):
        if district == "Maryland":
            tp = person.copy(deep=True)
        else:
            tp = person[person.district == district].copy(deep=True)

        if reform == "All Children":
            tp["total_ca"] = tp.spm_children * 100 * 12

        if reform == "Young Children":
            tp["total_ca"] = tp.spm_young_children * 100 * 12

        if reform == "Babies":
            tp["total_ca"] = tp.spm_babies * 1_000

        tp["new_resources"] = tp.total_ca + tp.spm_resources
        tp["still_poor"] = tp.new_resources < tp.spm_povthreshold

        # populations
        population = (tp.wt).sum()
        child_population = (tp.child * tp.wt).sum()
        young_child_population = (tp.young_child * tp.wt).sum()
        baby_population = (tp.baby * tp.wt).sum()

        # orginal poverty rates
        tp["poor"] = tp.spm_resources < tp.spm_povthreshold

        total_poor = (tp.poor * tp.wt).sum()
        total_pov_rate = total_poor / population

        total_child_poor = (tp.child * tp.poor * tp.wt).sum()
        child_pov_rate = total_child_poor / child_population

        total_young_child_poor = (tp.young_child * tp.poor * tp.wt).sum()
        young_child_pov_rate = total_young_child_poor / young_child_population

        total_baby_poor = (tp.baby * tp.poor * tp.wt).sum()
        baby_pov_rate = total_baby_poor / baby_population

        # new poverty rates
        new_total_poor = (tp.still_poor * tp.wt).sum()
        new_total_pov_rate = new_total_poor / population

        new_total_child_poor = (tp.child * tp.still_poor * tp.wt).sum()
        new_child_pov_rate = new_total_child_poor / child_population

        new_total_young_child_poor = (
            tp.young_child * tp.still_poor * tp.wt
        ).sum()
        new_young_child_pov_rate = (
            new_total_young_child_poor / young_child_population
        )

        new_total_baby_poor = (tp.baby * tp.still_poor * tp.wt).sum()
        new_baby_pov_rate = new_total_baby_poor / baby_population

        # percent change
        total_pov_change = (
            (new_total_poor - total_poor) / (total_poor) * 100
        ).round(1)
        child_pov_change = (
            (new_total_child_poor - total_child_poor)
            / (total_child_poor)
            * 100
        ).round(1)
        young_child_pov_change = (
            (new_total_young_child_poor - total_young_child_poor)
            / (total_young_child_poor)
            * 100
        ).round(1)
        baby_pov_change = (
            (new_total_baby_poor - total_baby_poor) / (total_baby_poor) * 100
        ).round(1)

        return pd.Series(
            [
                total_pov_change,
                child_pov_change,
                young_child_pov_change,
                baby_pov_change,
                population,
                child_population,
                young_child_population,
                baby_population,
                total_pov_rate,
                child_pov_rate,
                young_child_pov_rate,
                baby_pov_rate,
                new_total_pov_rate,
                new_child_pov_rate,
                new_young_child_pov_rate,
                new_baby_pov_rate,
            ]
        )

    districts = person.district.unique().tolist()
    summary = mdf.cartesian_product(
        {
            "reform": ["All Children", "Young Children", "Babies"],
            "district": ["Maryland"] + districts,
        }
    )

    def pov_row(row):
        return pov(row.reform, row.district)

    summary[
        [
            "total_pov_change",
            "child_pov_change",
            "young_child_pov_change",
            "baby_pov_change",
            "population",
            "child_population",
            "young_child_population",
            "baby_population",
            "total_pov_rate",
            "child_pov_rate",
            "young_child_pov_rate",
            "baby_pov_rate",
            "new_total_pov_rate",
            "new_child_pov_rate",
            "new_young_child_pov_rate",
            "new_baby_pov_rate",
        ]
    ] = summary.apply(pov_row, axis=1)

    pd.set_option("display.max_rows", None, "display.max_columns", None)

    return summary


if __name__ == "__main__":
    df = make_acs_md_county_df()
    df.to_csv("skeleton_district_data.csv")
