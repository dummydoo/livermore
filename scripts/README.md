# Livermore

Livermore is designed to find tri, quad and pent-arbitrage opportunities on one exchange.
It finds paths of trades which if executed will produce a profit. It focuses
on USDT -> USDT arb cycles.

It was found to be unprofitable after many, many hours of development. I have decided
to open source it in the hope that others may learn or profit from it.

It works by retrieving market prices and order book depths. It places prices into
a graph, and then we use a modified bellman-ford algorithm to find a negative
cycle between nodes. In this instance, a negative cycle will indicate a list of
trades which, when executed, should return a profit.

It takes into account the current binance fee. This value is stored in const.py.

It is based on the article by Kelvin Jiang found [here](https://www.kelvinjiang.com/2010/10/currency-arbitrage-in-99-lines-of-ruby.html).

There are a few basic components;
 - The main process. This program listens for market updates from a seperate ZMQ publisher, this publisher listens to websocket updates and pushes them to a socket. I have provided a simple publisher for the purposes of a public release; overhauling this should be your
 focus if you wish to use this code going forward.
 - Executor; the executor is a separate process. It listens for paths from Main. It then attempts to execute the path and report back. It is functional and will sell back to USDT if a path is not profitable.
 - Reporter; the reporter is a separate process. It listens for events and logs them to the database in a none-blocking way. Any process can write to
 the reporting queue. It's very simplistic and was in initial stages of development when this I stopped working on this project. It was not profiled.

 It was found that Market orders occasionally returned profits, but this was
 almost definitely just luck. Limit orders seem to show that we're far too slow
 to compete with C++, Java or Golang competition.

### Usage
`docker-compose -f docker/docker-compose-dev.yml up --build`

This will run dry mode. No trades will be executed, it will only log opportunities
and the possible (expected) profit.

Note; you may have to restart the bot service as it'll fail if postgres hasn't
previously been initialised.

To run for real, after modifying the config, just run:
`docker-compose -f docker/docker-compose-prod.yml up --build`

I recommend running on AWS Tokyo for ~2ms latency.

### Tests

To run tests use `python -m unittest discover app/test` - they are also run on each docker build.

### Concepts

Program concepts

 - Path - a Path is a list of currencies. If you start with currency[0] and exchange
   it for the currencies which follow, in order, you should end up with a profit.
 - Sellback / Missed path - This is what happens when we're too slow. There is no longer an
   `ask` at the price we wanted. Somebody got the opportunity before us and we were late. We
   need to sell back to USDT and look for another path.
 - Opportunity - an opportunity is a path which we decide to execute on.

### Todo

- [x] Fix orderbook. Returning 0.0 quantitiy. If quantity is 0.0 delete the key.
- [x] Write the path max quantity utility.
- [x] Test executing live
- [x] Move from market orders to limit orders in the execution system - fail fast.
- [ ] More test coverage
- [ ] Update the orderbook when we make trades - extra method to `app.orderbook.LimitOrderBook`
- [ ] More performance tests
- [x] Track events through code - assign uuid's for each opportunity - this will allow us to more easily link events together and perform analysis on system timings in production.
- [x] logs with very quick writes, we need to be able to work out how long we take from spotting an opportunity to executing it
- [ ] Optimisations


### Credits
 - Antonio Dudarev: some code reorganisation, some optimisation, profiling hacks (read stored data from text files)
 - Kelvin Jiang: Orginal Article
 - Callam Delaney: everything else
