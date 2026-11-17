from flask import Flask, jsonify, render_template_string

import requests

import time

app = Flask(__name__)

BASE = "https://api.india.delta.exchange"

SYMBOL = "BTCUSD"

HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport" content="width=device-width, initial-scale=1">

<title>Delta BTC Assistant</title>

<style>

body {background:#101522;color:white;font-family:Arial;padding:20px}

.card {background:#202b3d;padding:20px;border-radius:14px;margin:15px 0}

.price {font-size:32px;color:#36d399}

button {padding:12px;border:0;border-radius:8px;background:#2563eb;color:white}

</style>

</head>

<body>

<h2>Delta BTC Assistant</h2>

<div class="card">

<p>BTC Live Price</p>

<div class="price" id="price">Loading...</div>

<p id="status">Connecting to Delta Exchange...</p>

</div>

<div class="card">

<h3>Market Analysis</h3>

<p>5 Minute: <span id="m5">Loading</span></p>

<p>15 Minute: <span id="m15">Loading</span></p>

<p>1 Hour: <span id="h1">Loading</span></p>

</div>

<div class="card">

<h3>Trading Mode</h3>

<p>Paper analysis only. Real orders are disabled.</p>

<button onclick="loadData()">Refresh Data</button>

</div>

<script>

async function loadData(){

 try {

  const r = await fetch('/api/market');

  const d = await r.json();

  if(!r.ok) throw new Error(d.error || 'API error');

  document.getElementById('price').innerText =

    '$' + Number(d.price).toLocaleString();

  document.getElementById('status').innerText =

    'Live data received from Delta Exchange';

  document.getElementById('m5').innerText = d.trends['5m'];

  document.getElementById('m15').innerText = d.trends['15m'];

  document.getElementById('h1').innerText = d.trends['1h'];

 } catch(e) {

  document.getElementById('status').innerText = 'Connection error: ' + e.message;

 }

}

loadData();

setInterval(loadData, 30000);

</script>

</body>

</html>

"""

def get_candles(resolution):

    end = int(time.time())

    minutes = {"5m": 5, "15m": 15, "1h": 60}[resolution]

    start = end - minutes * 100 * 60

    response = requests.get(

        BASE + "/v2/history/candles",

        params={

            "resolution": resolution,

            "symbol": SYMBOL,

            "start": start,

            "end": end

        },

        timeout=15

    )

    response.raise_for_status()

    data = response.json()

    if not data.get("success"):

        raise ValueError("Delta candle API returned an error")

       candles = data["result"]
candles = sorted(candles, key=lambda c: int(c["time"]))
return candles

def get_trend(candles):

    closes = [float(c["close"]) for c in candles]

    if len(closes) < 21:

        return "Insufficient data"

    def ema(values, period):

        alpha = 2 / (period + 1)

        value = values[0]

        for x in values[1:]:

            value = alpha * x + (1-alpha) * value

        return value

    fast = ema(closes, 9)

    slow = ema(closes, 21)

    if fast > slow:

        return "Bullish"

    if fast < slow:

        return "Bearish"

    return "Neutral"

@app.route("/")

def home():

    return render_template_string(HTML)

@app.route("/api/market")

def market():

    try:

        ticker = requests.get(

            BASE + "/v2/tickers/" + SYMBOL,

            timeout=15

        )

        ticker.raise_for_status()

        result = ticker.json()["result"]

        price = result.get("close") or result.get("mark_price")

        if price is None:

            raise ValueError("Price unavailable")

        trends = {}

        for tf in ["5m", "15m", "1h"]:

            trends[tf] = get_trend(get_candles(tf))

        return jsonify(price=price, trends=trends)

    except Exception as e:

        return jsonify(error=str(e)), 502

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=10000)
