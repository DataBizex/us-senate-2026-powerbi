"""
Refresh script for the Senate 2026 Power BI project.
Builds the ACS 2020-2024 (vintage 2024, 5-year) state and county files from the official Census API,
and the FEC principal committee IDs for the Senate candidates in "Senate 2026 Candidate.csv".

Run in PowerShell from the folder that holds this script and the Senate 2026 CSV files:
    pip install requests
    $env:CENSUS_API_KEY="your_free_key"      # free key: https://api.census.gov/data/key_signup.html
    python "ACS refresh.py"

ACS values are 2020-2024 survey estimates. They are NOT 2026 data.
Suppressed Census values (negative codes such as -666666666) are written as blank, never estimated.
"""
import csv, io, os, sys, time, zipfile, datetime
import requests

KEY = os.environ.get("CENSUS_API_KEY", "")
YEAR = 2024
BASE = f"https://api.census.gov/data/{YEAR}/acs/acs5"
TODAY = datetime.date.today().isoformat()
VARS = {
    "B01003_001E": "population", "B01003_001M": "population_moe",
    "B19013_001E": "median_household_income", "B19013_001M": "median_household_income_moe",
    "B01002_001E": "median_age",
    "B17001_001E": "poverty_universe", "B17001_002E": "poverty_below",
    "B15003_001E": "edu_universe_25plus",
    "B15003_022E": "edu_bachelors", "B15003_023E": "edu_masters",
    "B15003_024E": "edu_professional", "B15003_025E": "edu_doctorate",
    "B03002_001E": "race_universe", "B03002_003E": "white_non_hispanic",
    "B03002_004E": "black_non_hispanic", "B03002_012E": "hispanic_any_race",
    "B25003_001E": "housing_units_occupied", "B25003_002E": "owner_occupied",
}

def clean(v):
    if v is None or v == "": return ""
    try:
        f = float(v)
    except ValueError:
        return ""
    return "" if f < 0 else (int(f) if f.is_integer() else f)

def transform(header, data, level):
    out = []
    idx = {h: i for i, h in enumerate(header)}
    for row in data:
        rec = {}
        if level == "county":
            rec["state_fips"] = row[idx["state"]].zfill(2)
            rec["county_fips"] = rec["state_fips"] + row[idx["county"]].zfill(3)
        else:
            rec["state_fips"] = row[idx["state"]].zfill(2)
        rec["name"] = row[idx["NAME"]]
        for code, label in VARS.items():
            rec[label] = clean(row[idx[code]])
        rec["acs_vintage"] = "2020-2024 5-year"
        rec["acs_table_year"] = YEAR
        rec["extraction_date"] = TODAY
        out.append(rec)
    return out

def fetch(level):
    get = "NAME," + ",".join(VARS)
    url = f"{BASE}?get={get}&for={'county:*&in=state:*' if level=='county' else 'state:*'}&key={KEY}"
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    j = r.json()
    return transform(j[0], j[1:], level)

def write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("wrote", path, len(rows), "rows")

def committees():
    """Principal campaign committee ID per candidate from the FEC candidate master (cn26)."""
    z = requests.get("https://www.fec.gov/files/bulk-downloads/2026/cn26.zip", timeout=300)
    z.raise_for_status()
    hdr = requests.get("https://www.fec.gov/files/bulk-downloads/data_dictionaries/cn_header_file.csv", timeout=60).text.strip().split(",")
    zf = zipfile.ZipFile(io.BytesIO(z.content))
    raw = zf.read(zf.namelist()[0]).decode("latin-1")
    ids = {r["fec_cand_id"] for r in csv.DictReader(open("Senate 2026 Candidate.csv", encoding="utf-8"))}
    out = []
    for row in csv.reader(io.StringIO(raw), delimiter="|"):
        rec = dict(zip(hdr, row))
        if rec.get("CAND_ID") in ids:
            out.append({"fec_cand_id": rec["CAND_ID"], "principal_committee_id": rec.get("CAND_PCC", ""),
                        "election_year": rec.get("CAND_ELECTION_YR", ""), "extraction_date": TODAY,
                        "source_file": "cn26.zip"})
    write("Senate 2026 Candidate Committee.csv", out)

if __name__ == "__main__":
    if not KEY:
        sys.exit("Set CENSUS_API_KEY first (free key from the Census Bureau).")
    write("Senate 2026 ACS State.csv", fetch("state"))
    time.sleep(1)
    write("Senate 2026 ACS County.csv", fetch("county"))
    committees()
