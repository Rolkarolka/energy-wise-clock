import pandas as pd
import datetime

if __name__ == "__main__":
    choosen_date = input(f"Input date to download: [{datetime.date.today()}]")
    if choosen_date == "":
        choosen_date = datetime.date.today()
    else:
        choosen_date = datetime.strptime(choosen_date)
    download_date = choosen_date.strftime('%Y%m%d')
    url = f"https://www.pse.pl/getcsv/-/export/csv/PL_GS/data/{download_date}"
    data = pd.read_csv(url, encoding="cp1250", sep=";")
    data.to_csv(f"resources/GS{download_date}.csv")
    url = f"https://www.pse.pl/getcsv/-/export/csv/PL_BPKD/data/{download_date}"
    data = pd.read_csv(url, encoding="cp1250", sep=";")
    data.to_csv(f"resources/BPKD{download_date}.csv")
