from modules.CognitiveFeedbackRouter import CognitiveFeedbackRouter

import asyncio

def main():
    cfr = CognitiveFeedbackRouter()
    asyncio.run(cfr.attention_switch())

if __name__ == '__main__':
    main()