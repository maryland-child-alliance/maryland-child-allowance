import pandas as pd
import numpy as np
import microdf as mdf
import plotly.express as px
from pathlib import Path
import os
import sys

def format_census_geo_col(col, location_type = 'county'):
    """
    This function takes a pandas series and adds leading zeros to the front of the
    census/fip columns, depending on which location type is specified 
    """
    # Change col data type to string
    col = col.astype(str)


    if location_type == 'state':
        col = col.str.zfill(2)
    elif location_type == 'county':
        col = col.str.zfill(3)
    elif location_type == 'tract':
        col = col.str.zfill(6)
    elif location_type == 'block group':
        col = col.str.zfill(7)
    elif location_type == 'block':
        col = col.str.zfill(5)
    
    return col

    