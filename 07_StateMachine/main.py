import asyncio

from spherov2 import scanner
from spherov2 import toy
from spherov2.sphero_edu import SpheroEduAPI

from states import (
    Caught,
    Chasing,
    Choosing,
    Evading,
    Initial,
    StateName,
    Terminal,
    TimedOut,
)


async def main(sphero):
    states = {
        StateName.INITIAL: Initial(sphero, StateName.INITIAL),
        StateName.CHOOSING: Choosing(sphero, StateName.CHOOSING),
        StateName.EVADING: Evading(sphero, StateName.EVADING),
        StateName.CHASING: Chasing(sphero, StateName.CHASING),
        StateName.CAUGHT: Caught(sphero, StateName.CAUGHT),
        StateName.TIMED_OUT: TimedOut(sphero, StateName.TIMED_OUT),
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

    # Run terminal state for one cycle
    await current_state.start()
    await current_state.execute()
    await current_state.stop()


if __name__ == "__main__":
    toy = scanner.find_toy(toy_name="SB-F11F")
    with SpheroEduAPI(toy) as sphero:
        try:
            asyncio.run(main(sphero))
        except KeyboardInterrupt:
            print("KeyboardInterrupt received, exiting...")
