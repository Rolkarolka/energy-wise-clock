import sys

from fastapi import FastAPI, WebSocket
from starlette.requests import Request
from fastapi.templating import Jinja2Templates
import asyncio
import pandas as pd
import uvicorn
from datetime import datetime, timedelta
import time


app = FastAPI()
templates = Jinja2Templates(directory="resources")
colors = {
    "ZALECANE UŻYTKOWANIE": "#105E27",
    "NORMALNE UŻYTKOWANIE": "#98FB98",
    "WYMAGANE OGRANICZANIE": "#DC143C",
    "ZALECANE OSZCZĘDZANIE": "#FBEC50"
}

def get_data(date, hour):
    gs_data = pd.read_csv(f"resources/GS{date}.csv", header=0)
    bpkd_data = pd.read_csv(f"resources/BPKD{date}.csv", header=0)
    if hour > 12:
        parsed_date = datetime.strptime(date, "%Y%m%d")
        next_parsed_day = parsed_date + timedelta(days=1)
        next_day = next_parsed_day.strftime("%Y%m%d")
        gs_next_data = pd.read_csv(f"resources/GS{next_day}.csv", header=0)
        gs_data = pd.concat([gs_data, gs_next_data])
        bpkd_next_data = pd.read_csv(f"resources/BPKD{next_day}.csv", header=0)
        bpkd_data = pd.concat([bpkd_data, bpkd_next_data])
    gs_selected_data = gs_data.iloc[hour:hour+12]
    bpkd_selected_data = bpkd_data.iloc[hour:hour+12]
    return gs_selected_data, bpkd_selected_data

def is_date(message):
    message = message.split(";")
    return len(message) == 2 and message[0].isnumeric() and message[1].isnumeric() and len(message[0]) == 8 and int(message[1]) <= 24

def get_energy_mix(hour_data):
    power_demand = hour_data["Krajowe zapotrzebowanie na moc"].values[0]
    green_energy = hour_data["Generacja źródeł wiatrowych"].values[0] + hour_data["Generacja źródeł fotowoltaicznych"].values[0]
    energy_for_country = hour_data["Krajowe saldo wymiany międzysystemowej równoległej"].values[0] + hour_data["Krajowe saldo wymiany międzysystemowej nierównoległej"].values[0]
    green_energy_percentage = green_energy / (power_demand - (energy_for_country)) * 100
    return round(green_energy_percentage, 2)

def prepare_color(gs_data):
    color = ";".join(["c"] + [colors[status] for status in list(gs_data['Godzina szczytu'])])
    return color

@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    date = datetime.now()
    year = date.strftime("%Y%m%d")
    hour = int(date.hour)
    gs_data, bpkd_data = get_data(year, hour)
    await websocket.accept()
    try:
        color = prepare_color(gs_data)
        await websocket.send_text(color)
        while True:
            # confirmation that client recived data, if there is no answer program stopped
            data = await asyncio.wait_for(websocket.receive_text(), timeout=5)

            if data.isnumeric():
                hour = int(data)
                hour_data = bpkd_data.loc[bpkd_data['Godzina'] == hour]
                green_energy_percentage = get_energy_mix(hour_data)
                await websocket.send_text(f"e;{green_energy_percentage};{100-green_energy_percentage}")
            elif is_date(data):
                year, hour = data.split(";")
                hour = int(hour)
                gs_data, bpkd_data = get_data(year, hour)
                color = prepare_color(gs_data)
                await websocket.send_text(color)
            time.sleep(1)
    except Exception:
        print("Connection closed")
    finally:
        # close the websocket
        await websocket.close()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
    # if "-d" in sys.argv[1:]:
    #     uvicorn.run(app, host="127.0.0.1", port=8000)
    # else:
    #     uvicorn.run(app, host="0.0.0.0", port=8000)
