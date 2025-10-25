import asyncio

from spherov2 import scanner
from spherov2 import toy
from spherov2.sphero_edu import SpheroEduAPI

from states import Initial, StateName, Terminal, Traveling


async def main(sphero):
    states = {
        StateName.INITIAL: Initial(sphero, StateName.INITIAL),
        StateName.TRAVELING: Traveling(sphero, StateName.TRAVELING),
        StateName.TERMINAL: Terminal(sphero, StateName.TERMINAL),
    }

    current_state = states[StateName.INITIAL]
    await current_state.start()

    while current_state.name != StateName.TERMINAL:
        result = await current_state.execute()

        if result:
            await current_state.stop()
            current_state = states[result]
            await current_state.start()

    print("Done")  # TODO run terminal state for a while


if __name__ == "__main__":
    toy = scanner.find_toy(toy_name="SB-F11F")
    with SpheroEduAPI(toy) as sphero:
        try:
            asyncio.run(main(toy))
        except KeyboardInterrupt:
            print("KeyboardInterrupt received, exiting...")
