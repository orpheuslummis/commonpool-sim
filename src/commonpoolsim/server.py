from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import json
from typing import List, Dict

app = FastAPI()

# Mount static files (we'll create these next)
app.mount("/static", StaticFiles(directory="src/commonpoolsim/static"), name="static")


class SimulationLogReader:
    def __init__(self, logs_dir: str = "simulation_logs"):
        self.logs_dir = Path(logs_dir)

    def get_all_simulations(self) -> List[Dict]:
        simulations = []
        for file in self.logs_dir.glob("*.json"):
            with open(file) as f:
                sim_data = json.load(f)
                simulations.append(
                    {
                        "id": sim_data["simulation_id"],
                        "start_time": sim_data["start_time"],
                        "participants": list(sim_data["initial_states"].keys()),
                        "exchanges": len(sim_data["exchanges"]),
                        "filename": file.name,
                    }
                )
        return sorted(simulations, key=lambda x: x["start_time"], reverse=True)

    def get_simulation_details(self, filename: str) -> Dict:
        try:
            with open(self.logs_dir / filename) as f:
                return json.load(f)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Simulation not found")


log_reader = SimulationLogReader()


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("src/commonpoolsim/static/index.html") as f:
        return f.read()


@app.get("/api/simulations")
async def list_simulations():
    return log_reader.get_all_simulations()


@app.get("/api/simulations/{filename}")
async def get_simulation(filename: str):
    return log_reader.get_simulation_details(filename)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
