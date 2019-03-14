# Coinbase - A Coinbase API written in Python3

## General Usage

To use authenticated methods, API keys are required.
Keys are not required for public methods.

The code is written to work with API keys stored as environment variables for security.

I suggest creating a keys.sh file to store your keys and running

```shell
source keys.sh
```

before using the API. Use this template file:

```shell
#!/bin/bash

################## CoinbasePro ##################

export Coinbase_KEY="-your private key-"
export Coinbase_KEY_PUBLIC="-your public key-"
export Coinbase_PASSPHRASE="-Coinbase passphrase-"

# if you're planning to use the Coinbase Sandbox

export Coinbase_KEY_SANDBOX="-sandbox private key-"
export Coinbase_KEY_PUBLIC_SANDBOX="-sandbox public key-"
export Coinbase_PASSPHRASE_SANDBOX="-Coinbase sandbox passphrase-"
```

.sh files are .gitignored to prevent keys from being posted or tracked by .git.

## Saving Historical Data

Data is saved in the following format:

Open time, close time, open price, high price, low price, close price, volume


The CoinbasePro API supports the following intervals:

1m, 5m, 15m

1h

1d


Sample usage:

```python
from coinbase import CoinbasePublic

coinbase = CoinbasePublic()

# symbol: BTCUSD (Bitcoin)
# dates: mm/dd/yy format
# interval: 1 day
hist = coinbase.get_history("BTC-USD", "01/01/18", "04/01/18", "1d")

# let's save this in a file called XRPBTC_daily.csv
coinbase.save_historical_data(hist, "BTCUSD_daily.csv")

# sample file saved in repository
```
