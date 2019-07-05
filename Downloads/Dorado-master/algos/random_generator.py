"""
Demo Code : Showing how to send signals to the bot
"""

from random import randint


class random_generator:

    def main(self, datalist):
        signal = randint(-1, 1)
        if signal == 1:
            return "buy"
        elif signal == -1:
            logging.debug("in getSignal, return sell signal")
            return "sell"
        else:
            return "hold"