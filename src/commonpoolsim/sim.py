from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol
from datetime import datetime
import asyncio
from dotenv import load_dotenv
import os
import litellm
import json
from pathlib import Path
import random

load_dotenv(".env.local")

os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY")
os.environ["AWS_REGION_NAME"] = os.getenv("AWS_REGION_NAME")


class LLMProvider:
    @staticmethod
    async def get_response(context: Dict) -> str:
        try:
            response = await litellm.acompletion(
                model="anthropic.claude-3-5-sonnet-20241022-v2:0",
                messages=[{"role": "user", "content": str(context)}],
                temperature=0.7,
                max_tokens=150,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error processing request: {str(e)}"


@dataclass
class TradeOffer:
    offered_items: Dict[str, int]
    requested_items: Dict[str, int]
    message: str = ""

    def to_dict(self) -> Dict:
        return {
            "offered_items": self.offered_items,
            "requested_items": self.requested_items,
            "message": self.message,
        }


class ExchangeOutcome:
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


@dataclass
class ExchangeRecord:
    timestamp: datetime
    initiator: str
    responder: str
    offer: TradeOffer
    facilitator_notes: str
    conversation: List[str]
    outcome: str
    final_terms: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "initiator": self.initiator,
            "responder": self.responder,
            "offer": self.offer.to_dict(),
            "facilitator_notes": self.facilitator_notes,
            "conversation": self.conversation,
            "outcome": self.outcome,
            "final_terms": self.final_terms,
        }


@dataclass
class Participant:
    name: str
    personality: str
    resources: Dict[str, int]
    needs: List[str]
    exchange_history: List[ExchangeRecord] = field(default_factory=list)

    async def consider_trade(
        self, offer: TradeOffer, facilitator_suggestion: str
    ) -> str:
        context = {
            "personality": self.personality,
            "resources": self.resources,
            "needs": self.needs,
            "offer": offer,
            "suggestion": facilitator_suggestion,
        }
        return await LLMProvider.get_response(context)

    def get_state(self) -> Dict:
        return {
            "name": self.name,
            "personality": self.personality,
            "resources": self.resources.copy(),
            "needs": self.needs.copy(),
            "exchange_count": len(self.exchange_history),
        }


class Facilitator:
    def __init__(self):
        self.exchange_history: List[ExchangeRecord] = []
        self.participant_notes: Dict[str, List[str]] = {}

    async def suggest_valuation(
        self, offer: TradeOffer, initiator: Participant, responder: Participant
    ) -> str:
        context = {
            "offer": offer,
            "initiator": initiator.get_state(),
            "responder": responder.get_state(),
            "recent_exchanges": [
                exchange.to_dict() for exchange in self.exchange_history[-5:]
            ],
        }
        return await LLMProvider.get_response(context)


@dataclass
class SimulationRecord:
    simulation_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    initial_states: Dict[str, Dict] = field(default_factory=dict)
    exchanges: List[ExchangeRecord] = field(default_factory=list)
    final_states: Dict[str, Dict] = field(default_factory=dict)
    summary: str = ""

    def to_dict(self) -> Dict:
        return {
            "simulation_id": self.simulation_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "initial_states": self.initial_states,
            "exchanges": [exchange.to_dict() for exchange in self.exchanges],
            "final_states": self.final_states,
            "summary": self.summary,
        }


class SimulationLogger:
    def __init__(self, output_dir: str = "simulation_logs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_record(self, record: SimulationRecord):
        filename = f"sim_{record.simulation_id}_{record.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        with open(filepath, "w") as f:
            json.dump(record.to_dict(), f, indent=2)


class CommonPoolExchange:
    def __init__(self, simulation_id: Optional[str] = None):
        self.participants: Dict[str, Participant] = {}
        self.facilitator = Facilitator()
        self.exchange_history: List[ExchangeRecord] = []
        self.simulation_id = simulation_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger = SimulationLogger()
        self.simulation_record = SimulationRecord(
            simulation_id=self.simulation_id, start_time=datetime.now()
        )

    def add_participant(
        self, name: str, personality: str, resources: Dict[str, int], needs: List[str]
    ):
        """Add a new participant to the system"""
        self.participants[name] = Participant(
            name=name, personality=personality, resources=resources, needs=needs
        )
        # Record initial state
        self.simulation_record.initial_states[name] = self.get_participant_state(name)

    async def initiate_exchange(
        self, initiator_name: str, responder_name: str, offer: TradeOffer
    ) -> ExchangeRecord:
        """Start and manage a new exchange process"""
        initiator = self.participants[initiator_name]
        responder = self.participants[responder_name]

        # Get facilitator suggestion
        facilitator_suggestion = await self.facilitator.suggest_valuation(
            offer, initiator, responder
        )

        # Get responder's consideration
        response = await responder.consider_trade(offer, facilitator_suggestion)

        # Create exchange record
        exchange = ExchangeRecord(
            timestamp=datetime.now(),
            initiator=initiator_name,
            responder=responder_name,
            offer=offer,
            facilitator_notes=facilitator_suggestion,
            conversation=[response],
            outcome=ExchangeOutcome.PENDING,  # You might want to determine this based on the response
        )

        # Add to histories
        self.exchange_history.append(exchange)
        initiator.exchange_history.append(exchange)
        responder.exchange_history.append(exchange)

        # Add to simulation record
        self.simulation_record.exchanges.append(exchange)

        return exchange

    async def generate_simulation_summary(self) -> str:
        context = {
            "initial_states": self.simulation_record.initial_states,
            "final_states": self.simulation_record.final_states,
            "num_participants": len(self.participants),
            "num_exchanges": len(self.exchange_history),
        }

        prompt = (
            "Provide a very brief summary (max 50 words) of this simulation's key patterns "
            "and outcomes. Compare initial and final states."
        )

        context["prompt"] = prompt
        return await LLMProvider.get_response(context)

    async def end_simulation(self):
        """End the simulation and save records"""
        self.simulation_record.end_time = datetime.now()

        # Record final states
        for name in self.participants:
            self.simulation_record.final_states[name] = self.get_participant_state(name)

        # Generate and add summary
        self.simulation_record.summary = await self.generate_simulation_summary()

        # Save to file
        self.logger.save_record(self.simulation_record)

    def get_participant_state(self, name: str) -> Dict:
        """Get current state of a participant"""
        p = self.participants[name]
        return {
            "name": p.name,
            "personality": p.personality,
            "resources": p.resources.copy(),
            "needs": p.needs.copy(),
            "exchange_count": len(p.exchange_history),
        }


# Example usage
async def main():
    # Create exchange system with specific simulation ID
    exchange = CommonPoolExchange(simulation_id="market_sim_001")

    # Simplified resources (reduced from 5 to 3)
    resources = {
        "books": (1, 2),
        "tools": (0, 2),
        "skills": (0, 2),  # Combined skills instead of separate types
    }

    # Simplified personalities (reduced from 5 to 3)
    personalities = [
        "generous",
        "cautious",
        "strategic",
    ]

    # Create 5 participants with simplified attributes
    participants = [
        {
            "name": f"P{i+1}",  # Shorter names
            "personality": random.choice(personalities),
            "resources": {
                resource: random.randint(min_val, max_val)
                for resource, (min_val, max_val) in resources.items()
                if random.random() > 0.4  # 60% chance to have each resource
            },
            "needs": random.sample(
                list(resources.keys()),
                k=1,  # Each participant needs exactly 1 resource
            ),
        }
        for i in range(5)
    ]

    # Add participants to exchange system
    for p in participants:
        exchange.add_participant(
            name=p["name"],
            personality=p["personality"],
            resources=p["resources"],
            needs=p["needs"],
        )

    # Reduced number of exchanges (from 8-12 to 5-7)
    num_exchanges = random.randint(5, 7)

    for _ in range(num_exchanges):
        # Randomly select initiator and responder
        available_participants = list(exchange.participants.keys())
        initiator = random.choice(available_participants)
        available_participants.remove(initiator)
        responder = random.choice(available_participants)

        # Create a trade offer based on participants' resources and needs
        initiator_participant = exchange.participants[initiator]
        responder_participant = exchange.participants[responder]

        # Only offer resources the initiator has
        available_to_offer = {
            resource: amount
            for resource, amount in initiator_participant.resources.items()
            if amount > 0
        }

        if available_to_offer and responder_participant.needs:
            # Create offer
            offered_resource = random.choice(list(available_to_offer.keys()))
            offered_amount = random.randint(1, available_to_offer[offered_resource])

            # Request something the initiator needs
            requested_resource = random.choice(initiator_participant.needs)
            requested_amount = random.randint(1, 2)

            offer = TradeOffer(
                offered_items={offered_resource: offered_amount},
                requested_items={requested_resource: requested_amount},
                message=f"Would you be interested in trading {offered_amount} {offered_resource} for {requested_amount} {requested_resource}?",
            )

            # Initiate exchange
            result = await exchange.initiate_exchange(initiator, responder, offer)

            # Optional: Update resources based on exchange outcome
            if result.outcome == ExchangeOutcome.SUCCESS:
                # Update resources (you might want to implement this in the ExchangeRecord class)
                pass

    # End simulation and save records
    await exchange.end_simulation()

    # Print summary
    print(f"\nSimulation Summary:")
    print(f"Number of participants: {len(exchange.participants)}")
    print(f"Number of exchanges: {len(exchange.exchange_history)}")
    print("\nFinal States:")
    for name, participant in exchange.participants.items():
        state = exchange.get_participant_state(name)
        print(f"\n{name} ({state['personality']}):")
        print(f"Resources: {state['resources']}")
        print(f"Needs: {state['needs']}")
        print(f"Exchanges participated in: {state['exchange_count']}")

    # Also print the simulation summary
    print("\nSimulation Analysis:")
    print(exchange.simulation_record.summary)


if __name__ == "__main__":
    asyncio.run(main())
