class LivermoreException(Exception):
    pass

class NoMarketError(LivermoreException):
    """raised by algo.give_pair_market_direction() if we cannot find the market."""
    pass

class OrderBookError(LivermoreException):
    pass

class QuantityTooSmallError(LivermoreException):
    """ raised by the closest_tradeable_quantity() method if the quantity is too small."""
    pass

class TooSlowException(LivermoreException):
    pass
