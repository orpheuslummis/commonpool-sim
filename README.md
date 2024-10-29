# CommonPool Exchange Simulation

A simulation environment for studying peer-to-peer exchange dynamics in communities, powered by AI-assisted participants and facilitators.

## Overview

CommonPool Exchange Simulation creates a virtual marketplace where AI participants with distinct personalities engage in bilateral bartering. Each exchange is supported by an AI facilitator that can suggest (but not enforce) valuations, creating a rich environment for studying trading patterns and social dynamics.

## Features

- **AI-Powered Participants**
  - Unique personalities (cautious, generous, strategic)
  - Individual resource portfolios
  - Specific needs and wants
  - Trading history tracking

- **Intelligent Facilitation**
  - Context-aware trade suggestions
  - Historical pattern recognition
  - Non-binding valuations
  - Detailed exchange records

- **Flexible Simulation Parameters**
  - Configurable number of participants
  - Adjustable exchange counts
  - Customizable resource types
  - Detailed logging and analysis

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/commonpoolsim.git
cd commonpoolsim

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your API keys
```

## Usage

### Running a Simulation

```bash
# Basic simulation with default parameters
python src/commonpoolsim/sim.py

# Custom simulation with specific parameters
python src/commonpoolsim/sim.py \
  --num-participants 10 \
  --min-exchanges 8 \
  --max-exchanges 12 \
  --simulation-id custom_sim_001 \
  --output-dir custom_logs
```

### Viewing Results

```bash
# Start the web interface
python src/commonpoolsim/server.py

# Open in browser
open http://localhost:8000
```

## API Endpoints

The web interface provides the following API endpoints:

- `GET /api/simulations` - List all simulation runs
- `GET /api/simulations/{filename}` - Get detailed results for a specific simulation

## Configuration

Key simulation parameters can be adjusted through command-line arguments:

- `--num-participants`: Number of trading participants
- `--min-exchanges`: Minimum number of exchanges to simulate
- `--max-exchanges`: Maximum number of exchanges to simulate
- `--simulation-id`: Custom identifier for the simulation run
- `--output-dir`: Directory for simulation logs

## Project Structure

```
commonpoolsim/
├── src/
│   └── commonpoolsim/
│       ├── sim.py         # Core simulation logic
│       ├── server.py      # Web interface and API
│       └── static/        # Web interface assets
├── simulation_logs/       # Simulation output directory
├── .env.local            # Local environment configuration
└── README.md
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)

## Acknowledgments

- Built with FastAPI and LiteLLM
- Inspired by research in peer-to-peer economies and social trading systems
```

This project is part of ongoing research into community-based exchange systems and social trading dynamics. For more detailed information about the system's design and philosophy, please see NOTES.md.